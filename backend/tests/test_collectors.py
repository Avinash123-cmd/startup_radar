from collectors.github_collector import collect_github
from collectors.ph_collector import collect_ph
from collectors.reddit_collector import collect_reddit


def test_credentialed_collectors_skip_without_credentials():
    settings = {
        "collectors_limit": 1,
        "github_token": "",
        "reddit_client_id": "",
        "reddit_client_secret": "",
        "product_hunt_token": "",
    }

    github = collect_github(settings=settings)
    reddit = collect_reddit(settings=settings)
    product_hunt = collect_ph(settings=settings)

    assert github.status == "skipped"
    assert reddit.status == "skipped"
    assert product_hunt.status == "skipped"
    assert github.records == []
    assert reddit.records == []
    assert product_hunt.records == []
