from rest_framework.pagination import CursorPagination


class MessageCursorPagination(CursorPagination):
    ordering = "-created_at"
    page_size = 50
    page_size_query_param = "limit"
    max_page_size = 100


class ThreadCursorPagination(CursorPagination):
    ordering = "created_at"
    page_size = 50
    page_size_query_param = "limit"
    max_page_size = 100


class NotificationCursorPagination(CursorPagination):
    ordering = "-created_at"
    page_size = 30
    page_size_query_param = "limit"
    max_page_size = 100
