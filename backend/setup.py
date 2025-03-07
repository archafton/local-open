from setuptools import setup, find_packages

setup(
    name="congressgov",
    version="0.1.0",
    packages=find_packages(where="src/python"),
    package_dir={"": "src/python"},
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "bill-fetch=congressgov.bill_fetch.bill_fetch_core:main",
            "bill-detail=congressgov.bill_fetch.bill_detail_processor:main",
            "bill-batch=congressgov.bill_fetch.bill_batch_processor:main",
            "bill-validate=congressgov.bill_fetch.bill_validation:main",
            "member-fetch=congressgov.members_fetch.member_fetch_core:main",
            "member-detail=congressgov.members_fetch.member_detail_processor:main",
            "member-enrich=congressgov.members_fetch.member_enrichment:main",
            "member-bio=congressgov.members_fetch.member_bio:main",
        ],
    },
)
