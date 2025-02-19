# apps/trains/docs/api_requirements.py

AI_SERVICE_REQUIREMENTS = {
    'endpoints': {
        'crowd_detection': '/api/detect-crowd',
        'prediction': '/api/predict-crowd'
    },
    'authentication': 'Bearer token',
    'response_format': {
        'passenger_count': 'integer',
        'confidence_score': 'float',
        'timestamp': 'ISO format datetime'
    }
}
