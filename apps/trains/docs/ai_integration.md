# apps/trains/docs/ai_integration.md

## AI Integration Guide

## Overview

This document describes the integration points between the Metro system and the AI crowd detection service.

## Endpoints

- Crowd Detection: `/api/detect-crowd`
- Crowd Prediction: `/api/predict-crowd`

## Authentication

Bearer token authentication is required for all AI service endpoints.

## Data Formats

### Request Format

```json
{
    "camera_id": "string",
    "timestamp": "ISO datetime",
    "image_data": "base64 string"
}
