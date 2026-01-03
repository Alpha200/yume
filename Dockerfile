# Multi-stage build for Vue.js frontend and Spring Boot backend

# Stage 1: Build Vue.js frontend
FROM node:24-alpine AS frontend-builder

WORKDIR /app/ui

# Copy package files
COPY ui/package*.json ./
RUN npm ci

# Copy source code and build
COPY ui/ ./
RUN npm run build

# Stage 2: Build Spring Boot backend
FROM gradle:8.5-jdk21 AS backend-builder

WORKDIR /app/backend

# Copy Spring Boot project
COPY yume-spring/ ./

# Build the Spring Boot application
RUN gradle bootJar --no-daemon

# Stage 3: Runtime with Nginx, Spring Boot, and built frontend
FROM eclipse-temurin:21-jre-alpine

# Install Nginx and bash (for wait -n support)
RUN apk add --no-cache nginx bash

WORKDIR /app

# Copy Spring Boot JAR from builder
COPY --from=backend-builder /app/backend/build/libs/*.jar ./app.jar

# Copy built frontend from frontend builder
COPY --from=frontend-builder /app/ui/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Set default port for Spring Boot
ENV SERVER_PORT=8080

# Expose port for Nginx
EXPOSE 8079

# Run both processes; exit container if either dies
CMD ["/bin/bash", "-c", "java -jar app.jar & nginx -g 'daemon off;' & wait -n"]
