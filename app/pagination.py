from fastapi import Request


# Pagination کلاس ساختگی یا استفاده از پکیج
class DefaultPagination:
    def paginate_queryset(self, queryset, request: Request, page_size: int = 10):
        # پیاده‌سازی ساده برای pagination
        limit = int(request.query_params.get("limit", page_size))
        offset = int(request.query_params.get("offset", 0))
        return queryset[offset : offset + limit]

    def get_paginated_response(self, data, request: Request):
        return {"results": data}


def customDecoder(dict_obj):
    # تبدیل custom json به object
    return dict_obj  # فرض بر این است که کد اصلی شما داخل این تابع قرار دارد
