# Java MongoDB Demo

Small **Spring Boot + MongoDB** demo app with CRUD endpoints for a `people` collection.

## Prereqs

- Java 21+
- Docker (for MongoDB)

## Run MongoDB

```bash
docker compose up -d
```

Mongo will be available at `mongodb://localhost:27017/demo`.

## Run the app

```bash
mvn spring-boot:run
```

App runs on `http://localhost:8080`.

## API

Base path: `/api/people`

### Create a person

```bash
curl -sS -X POST "http://localhost:8080/api/people" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","age":36}'
```

### List people

```bash
curl -sS "http://localhost:8080/api/people"
```

### Get by id

```bash
curl -sS "http://localhost:8080/api/people/<id>"
```

### Update

```bash
curl -sS -X PUT "http://localhost:8080/api/people/<id>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","age":37}'
```

### Delete

```bash
curl -sS -X DELETE "http://localhost:8080/api/people/<id>" -i
```

## Configuration

- **Mongo URI**: set `MONGODB_URI` (defaults to `mongodb://localhost:27017/demo`)
