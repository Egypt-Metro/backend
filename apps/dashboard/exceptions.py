# apps/dashboard/exceptions.py
class DashboardServiceError(Exception):
    """Base exception for dashboard service errors"""
    pass


class ModelImportError(DashboardServiceError):
    """Raised when model import fails"""
    pass


class ReportGenerationError(DashboardServiceError):
    """Raised during report generation failures"""
    pass
