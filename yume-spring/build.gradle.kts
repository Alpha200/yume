import org.gradle.util.GradleVersion.version

plugins {
	kotlin("jvm") version "2.2.21"
	kotlin("plugin.spring") version "2.2.21"
	kotlin("plugin.serialization") version "2.2.21"
	id("org.springframework.boot") version "3.5.9"
	id("io.spring.dependency-management") version "1.1.7"
}

group = "eu.sendzik"
version = "0.0.1-SNAPSHOT"
description = "Yume"

java {
	toolchain {
		languageVersion = JavaLanguageVersion.of(21)
	}
}

repositories {
	mavenCentral()
}

val trixnityVersion = "4.22.7"
val kotlinxSerializationVersion = "1.9.0"
val ktorVersion = "3.3.3"
val kotlinLoggingVersion = "7.0.13"
val langChain4jVersion = "1.10.0-beta18"
val calDav4jVersion = "1.0.5"
val chromaClientVersion = "1.1.0"
val caffeineCacheVersion = "3.2.3"
val mockkVersion = "1.14.7"

dependencies {
	implementation("org.springframework.boot:spring-boot-starter-web")
	implementation("org.jetbrains.kotlin:kotlin-reflect")

	// Langchain4j dependencies
	implementation("dev.langchain4j:langchain4j-open-ai-spring-boot-starter:$langChain4jVersion")
	implementation("dev.langchain4j:langchain4j-spring-boot-starter:$langChain4jVersion")
	implementation("dev.langchain4j:langchain4j-kotlin:$langChain4jVersion")
	implementation("dev.langchain4j:langchain4j-open-ai-official:$langChain4jVersion") // Embedding
	implementation("dev.langchain4j:langchain4j-pgvector:$langChain4jVersion")
	runtimeOnly("com.fasterxml.jackson.module:jackson-module-kotlin")


	// Matrix SDK dependency
	implementation("net.folivo:trixnity-client:$trixnityVersion")
	implementation("io.ktor:ktor-client-apache5:$ktorVersion")
	// Need to align kotlinx serialization version with spring boot and ktor
	implementation("org.jetbrains.kotlinx:kotlinx-serialization-core-jvm:${kotlinxSerializationVersion}")
	implementation("org.jetbrains.kotlinx:kotlinx-serialization-json-io-jvm:${kotlinxSerializationVersion}")
	implementation("org.jetbrains.kotlinx:kotlinx-serialization-json-jvm:${kotlinxSerializationVersion}")

	// Calendar
	implementation("com.github.caldav4j:caldav4j:$calDav4jVersion")
	// Commons Lang3 (forced version due to CVE)
	implementation("org.apache.commons:commons-lang3:3.20.0")

	// Kotlin logging
	implementation("io.github.oshai:kotlin-logging-jvm:$kotlinLoggingVersion")


	// Spring data
	implementation("org.springframework.boot:spring-boot-starter-data-mongodb")

	// Spring Security
	implementation("org.springframework.boot:spring-boot-starter-oauth2-resource-server")

	// Spring Boot Caching
	implementation("org.springframework.boot:spring-boot-starter-cache")
	implementation("com.github.ben-manes.caffeine:caffeine:$caffeineCacheVersion")

	// Observability (Spring Boot 4)
	//implementation("org.springframework.boot:spring-boot-starter-actuator")
	//implementation("org.springframework.boot:spring-boot-starter-opentelemetry")
	//implementation("io.micrometer:micrometer-tracing-bridge-otel")
	//implementation("io.opentelemetry:opentelemetry-exporter-otlp")

	// Testing dependencies
	testImplementation("org.springframework.boot:spring-boot-starter-test")
	testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
	testImplementation("io.mockk:mockk:${mockkVersion}")
	testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
	compilerOptions {
		freeCompilerArgs.addAll("-Xjsr305=strict")
		javaParameters = true
	}
}

tasks.withType<Test> {
	useJUnitPlatform()
}
