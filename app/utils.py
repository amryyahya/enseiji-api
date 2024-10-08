def filter_by_date(start_date, end_date):
    date_filter = {}
    if start_date:
        date_filter['$gte'] = start_date
    if end_date:
        date_filter['$lte'] = end_date
    return date_filter

def filter_by_amount(min_amount, max_amount):
    amount_filter = {}
    if min_amount:
        amount_filter['$gte'] = float(min_amount)
    if max_amount:
        amount_filter['$lte'] = float(max_amount)
    return amount_filter

def build_pipeline(user, unwind, match_conditions, sort_by, sort_order, skip, limit):
    pipeline = [
        {'$match': {'username': user}},
        {'$unwind':f'${unwind}'},
        {'$match': match_conditions},
        {'$sort': {sort_by: sort_order}},
        {'$skip': skip},
        {'$limit': limit},
    ]
    return pipeline