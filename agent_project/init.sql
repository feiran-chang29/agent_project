-- init.sql

-- Roles
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'project4_owner') THEN
    CREATE ROLE project4_owner NOLOGIN;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'project4_app') THEN
    CREATE ROLE project4_app
      LOGIN
      PASSWORD 'project4_minimal'
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE
      NOREPLICATION
      INHERIT;
  ELSE
    ALTER ROLE project4_app
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE
      NOREPLICATION;
  END IF;
END
$$;

-- Schema
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'app') THEN
    EXECUTE 'CREATE SCHEMA app AUTHORIZATION project4_owner';
  END IF;
END
$$;

-- Table
CREATE TABLE IF NOT EXISTS app.tasks (
  task_id        uuid PRIMARY KEY,
  status         text NOT NULL,
  input_payload  jsonb NOT NULL,
  output_payload jsonb,
  error          text,
  created_at     timestamptz NOT NULL DEFAULT now(),

  request_id     uuid NOT NULL,
  request_host   text NOT NULL,
  request_port   text NOT NULL,

  updated_at     timestamptz,

  CONSTRAINT tasks_status_check
    CHECK (status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text]))
);

ALTER TABLE app.tasks OWNER TO project4_owner;

-- Privileges
GRANT CONNECT ON DATABASE project4_minimal TO project4_app;

-- 关键：app user 只能 USAGE，不给 CREATE
REVOKE ALL ON SCHEMA app FROM PUBLIC;
REVOKE ALL ON SCHEMA app FROM project4_app;
GRANT USAGE ON SCHEMA app TO project4_app;

GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA app
  TO project4_app;

ALTER DEFAULT PRIVILEGES FOR ROLE project4_owner IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO project4_app;
