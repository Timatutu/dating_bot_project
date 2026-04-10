# Dating Bot
### Telegram Bot + Mini App + FastAPI
`aiogram 3.x` · `FastAPI` · `PostgreSQL` · `Redis` · `RabbitMQ` · `Celery` · `MinIO`

---

## Содержание

1. [Идея проекта](#1-идея-проекта)
2. [Архитектура системы](#2-архитектура-системы)
3. [Технологический стек](#3-технологический-стек)
4. [Алгоритм ранжирования](#4-алгоритм-ранжирования)
5. [Схема базы данных](#5-схема-базы-данных)
6. [Маршрут пользователя](#6-маршрут-пользователя)
7. [Лимит свайпов и подписка](#7-лимит-свайпов-и-подписка)
8. [Метрики и логирование](#8-метрики-и-логирование)
9. [Этапы разработки](#9-этапы-разработки)
10. [Система оценивания](#10-система-оценивания)
11. [PlantUML диаграммы](#11-plantuml-диаграммы)

---

## 1. Идея проекта

Dating Bot — Telegram-приложение для знакомств. Пользователь **не выходит из Telegram**: всё происходит через бота и встроенный Mini App — не нужно скачивать отдельное приложение или создавать новый аккаунт.

**Три основы системы:**

- **Умное ранжирование** — анкеты показываются по трёхуровневому алгоритму: заполненность профиля, активность и частота лайков от других. Чем активнее профиль — тем выше он в ленте.
- **Мэтч → @username сразу** — при взаимном лайке оба пользователя получают username партнёра и могут написать напрямую в Telegram.
- **Монетизация через ценность** — Premium-подписка: безлимитный просмотр (без неё 50 анкет в сутки) и буст позиции в ленте.

**Целевая аудитория:** активные пользователи Telegram 18–45 лет, ищущие знакомств в своём городе.

---

## 2. Архитектура системы

Микросервисная архитектура. Сервисы общаются через RabbitMQ (события) и HTTP (запросы от Mini App). Каждый сервис — отдельный Docker-контейнер.

### Слои

| Слой | Компоненты |
|---|---|
| **Client** | Telegram Bot · Telegram Mini App (WebApp) |
| **Application** | Bot Service (aiogram 3.x) · API Service (FastAPI) |
| **Messaging** | RabbitMQ: `like.event` `match.created` `sub.activated` `feed.reload` |
| **Cache** | Redis: `feed:{id}` `swipes:{id}:date` · FSM state |
| **Data** | PostgreSQL · MinIO/S3 · Celery Worker |
| **Monitoring** | Prometheus · Grafana · structlog |

### Сервисы

| Сервис | Технология | Роль | Порт |
|---|---|---|---|
| Bot Service | aiogram 3.x | Команды, FSM анкеты, уведомления о мэтче | 8080 |
| API Service | FastAPI | REST для Mini App, HMAC авторизация | 8000 |
| Mini App | Telegram WebApp | Свайп-интерфейс, чат, оплата | — |
| Celery Worker | Celery + Beat | Рейтинг, буст, подгрузка кэша | — |
| RabbitMQ | RabbitMQ 3 | Брокер очередей событий | 5672 |
| Redis | Redis 7 | Кэш ленты, счётчик свайпов, FSM state | 6379 |
| PostgreSQL | PostgreSQL 16 | Основное хранилище | 5432 |
| MinIO | MinIO (S3) | Хранилище фотографий | 9000 |
| Nginx | Nginx | Reverse proxy | 80 / 443 |
| Prometheus | Prometheus | Сбор метрик | 9090 |
| Grafana | Grafana | Дашборды | 3000 |

### Структура репозитория

| Директория | Содержимое |
|---|---|
| `bot/` | dispatcher, роутеры (start, profile, swipe, subscription, match), middleware |
| `api/` | FastAPI приложение, роутеры (feed, like, match, subscription, payment) |
| `workers/` | Celery задачи и Beat расписание |
| `mini_app/` | React Web App |
| `infra/` | docker-compose.yml, nginx.conf |
| `.github/` | GitHub Actions CI/CD |

---

## 3. Технологический стек

| Технология | Зачем |
|---|---|
| **Python 3.12** | Весь бэкенд, нативный async/await |
| **aiogram 3.x** | FSM, роутеры, RedisStorage для состояний |
| **FastAPI** | Async REST API, pydantic v2, OpenAPI |
| **PostgreSQL 16** | ACID, UUID PK, индексы на `combined_score` |
| **SQLAlchemy 2.0** | Async ORM, миграции через Alembic |
| **Redis 7** | Атомарный INCR, EXPIREAT, FSM state |
| **RabbitMQ 3** | Durable очереди с ack, развязка сервисов |
| **Celery 5 + Beat** | Фоновые задачи, периодический пересчёт |
| **MinIO** | S3-совместимое хранилище, presigned URL |
| **Docker Compose** | Контейнеризация, единая сеть |
| **Prometheus + Grafana** | Метрики и дашборды |
| **structlog** | JSON-логи с контекстом |
| **GitHub Actions** | CI/CD: линтер, тесты, деплой |
| **YooKassa** | Оплата картой и СБП через webhook |
| **Telegram Stars** | Встроенная оплата через Telegram |
| **Alembic** | Версионирование схемы БД |

---

## 4. Алгоритм ранжирования

### Формула

`combined = primary × 0.4 + behavioral × 0.6 + subscription_boost`

| Уровень | Вес | Факторы |
|---|---|---|
| **Primary** | ×0.4 | Полнота анкеты (фото, bio, город), соответствие фильтрам других |
| **Behavioral** | ×0.6 | Лайки (+1.0), скипы (−0.3), матчи (+2.0), инициирование диалога (+1.5), рефералы (+3.0) |
| **Premium boost** | +50 flat | Активна пока `subscription.status = active`. Снимается Celery Beat при истечении |

**Пример:** primary=70, behavioral=80, подписка активна → `70×0.4 + 80×0.6 + 50 = 126` — высокий приоритет.

### Поиск анкет (конвейер)

1. **Жёсткие фильтры** — исключить просмотренных, несовпадающий пол/возраст/геолокацию (Haversine)
2. **Взаимная совместимость** — фильтры B должны подходить под профиль A
3. **Сортировка** — `ORDER BY combined_score DESC`
4. **Кэш** — топ-10 в Redis `feed:{user_id}` TTL 5 мин
5. **Предзагрузка** — на 8-й анкете Celery уже готовит следующий батч

---

## 5. Схема базы данных

| Таблица | Ключевые поля |
|---|---|
| `users` | id uuid PK, telegram_id bigint UK, username, sub_expires_at |
| `profiles` | id, user_id FK, name, age, gender, bio, city, lat, lng, photos_count |
| `photos` | id, profile_id FK, s3_key, is_primary, position |
| `ratings` | id, user_id FK UK, primary_score, behavioral_score, combined_score |
| `likes` | id, from_user FK, to_user FK, action (like/skip), INDEX(from,to) |
| `matches` | id, user1_id FK, user2_id FK, is_active |
| `messages` | id, match_id FK, sender_id FK, content, sent_at |
| `subscriptions` | id, user_id FK, plan, status (pending/active/expired), expires_at |
| `payments` | id, sub_id FK, amount, provider (yookassa/tg_stars), provider_id, status |

**Связи:** `users→profiles→photos`, `users→ratings`, `users↔users` через `likes/matches`, `matches→messages`, `users→subscriptions→payments`

---

## 6. Маршрут пользователя

### Регистрация и анкета

| Шаг | Актор | Действие |
|---|---|---|
| 1 | User | `/start` → Bot Service |
| 2 | Bot | Проверяет telegram_id → `INSERT users` |
| 3 | User | «Создать анкету» → FSM: имя → возраст → пол → город → bio → фото |
| 4 | Bot | Фото → MinIO, `s3_key` → PostgreSQL |
| 5 | RabbitMQ | `profile.created` → Celery считает `primary_score` |

### Лента и лайк

| Шаг | Актор | Действие |
|---|---|---|
| 1 | User | «Смотреть анкеты» → `GET /api/feed` |
| 2 | FastAPI | Проверяет лимит → Redis `feed:{id}` (cache-aside) |
| 3 | User | Свайп → `POST /api/like` |
| 4 | FastAPI | `INSERT likes` → проверяет встречный лайк |
| 5 | RabbitMQ | `like.event` → Celery обновляет `behavioral_score` |

### Мэтч

| Шаг | Актор | Действие |
|---|---|---|
| 1 | FastAPI | Встречный лайк найден → `INSERT matches` + `match.created` в RabbitMQ (одна транзакция) |
| 2 | Bot | Consumer получает событие → `SELECT username` обоих |
| 3 | Bot | `send_message` обоим параллельно: «Мэтч! @username_партнёра» |

> Нет `@username` → бот отправляет `tg://user?id={telegram_id}`

---

## 7. Лимит свайпов и подписка

### Лимит

| | Без подписки | Premium |
|---|---|---|
| Свайпов в сутки | 50 | Безлимитно |
| Хранение | Redis `swipes:{id}:YYYY-MM-DD` INCR | Проверка `sub_expires_at > now()` |
| Сброс | EXPIREAT 00:00 UTC (автоматически) | — |
| При исчерпании | HTTP 429 + кнопка «Premium» | — |

### Подписка

**Преимущества:** снятие лимита + +50 к `combined_score`

**Провайдеры:**
- **YooKassa** — карты, СБП, подтверждение через webhook `POST /api/payments/yookassa`
- **Telegram Stars** — встроенная валюта, подтверждение через `successful_payment` в aiogram

**Жизненный цикл:** `pending` → оплата → webhook → `active` + `sub_expires_at` → Celery: +50 boost → инвалидация Redis

---

## 8. Метрики и логирование

**Prometheus:** HTTP latency p50/p95/p99, RPS, ошибки Celery, глубина очередей RabbitMQ

**Grafana дашборды:** DAU/MAU, конверсия просмотры→лайки→матчи, revenue по провайдерам, технические метрики

**structlog:** JSON-логи с контекстом `user_id`, `trace_id`. Только бизнес-события и ошибки — не каждый запрос.

---

## 9. Этапы разработки

### Этап 1 — Планирование и проектирование

Создание описания сервисов, проектирование архитектуры, схема БД, настройка git-репозитория. Результат: документация, ERD, docker-compose с базовой конфигурацией всех сервисов.

### Этап 2 — Базовая функциональность бота

Реализация Bot Service на aiogram 3.x: обработка команды `/start`, регистрация пользователя по `telegram_id`, главное меню с WebApp-кнопками. Подключение PostgreSQL через SQLAlchemy, базовые миграции через Alembic.

### Этап 3 — Анкеты и хранилище фото

FSM-сценарий заполнения анкеты (имя → возраст → пол → город → bio → фото), загрузка фотографий в MinIO, сохранение `s3_key` в БД. Подключение Redis как RedisStorage для FSM-состояний.

### Этап 4 — Алгоритм ранжирования и лента

Реализация трёхуровневого рейтинга: `primary_score` при создании профиля, `behavioral_score` через Celery-воркер, `combined_score` по формуле. Подключение RabbitMQ: очереди `profile.created` и `like.event`. Кэширование ленты в Redis с предзагрузкой на 8-й анкете.

### Этап 5 — Лайки, матчи и уведомления

Эндпоинт `POST /api/like` с атомарной проверкой встречного лайка, создание матча и публикация `match.created` в одной транзакции. Bot Service consumer — отправка `@username` обоим пользователям параллельно. Лимит 50 свайпов в сутки через Redis `INCR` + `EXPIREAT`.

### Этап 6 — Подписка и платежи

Интеграция YooKassa (webhook) и Telegram Stars (`successful_payment`). Жизненный цикл платежа: `pending → active`, обновление `sub_expires_at`, буст +50 к рейтингу через Celery. Снятие лимита свайпов для Premium-пользователей.

### Этап 7 — Мониторинг, тесты и деплой

Подключение Prometheus и Grafana, настройка дашборды. Структурированное логирование через structlog. Настройка GitHub Actions: линтер ruff, тесты pytest, сборка Docker-образов, деплой. Нагрузочное тестирование через Apache JMeter.

---
