## ADDED Requirements

### Requirement: Service catalogue covers all impuestito.org non-adult categories
The system SHALL register services for all categories on impuestito.org except "Adultos" and "Créditos para Videojuegos". The full list covers: Cine/Series/TV, Música, Videojuegos, Deportes, Chatbots IA, Asistentes de Código IA, Vibe Coding, Generación Visual IA, Hosting/Cloud, Diseño, Seguridad, Productividad, Almacenamiento, Redes Sociales/Chat, and Aprendizaje.

#### Scenario: All expected services are registered on startup
- **WHEN** `init_db()` runs on a fresh database
- **THEN** the `servicemeta` table contains at least 114 rows with distinct `id` values

#### Scenario: Each service has a valid impuestito.org slug
- **WHEN** a scrape is triggered for any registered service
- **THEN** the scraper constructs a URL matching `https://www.impuestito.org/suscripciones/<slug>` and fetches it without a 404

### Requirement: Each service exposes a category in the API response
The system SHALL include a non-empty `category` string on every `ServiceOut` object, matching the impuestito.org section the service belongs to (e.g., "Cine, Series y TV", "Música", "Videojuegos").

#### Scenario: API response includes category field
- **WHEN** a client calls `GET /api/v1/prices`
- **THEN** every object in `services` has a `category` field that is a non-empty string

#### Scenario: Category is preserved across scrape updates
- **WHEN** a scrape cycle completes and updates a service's prices
- **THEN** the `category` field on that service remains unchanged in the next API response
