def format_endpoint(endpoint, **kwargs):
    """   Fill in place holders in endpoint with actual paramters
        format_endpoint(Account.BY_PUUID, puuid="...")
    """
    return endpoint.format(**kwargs)