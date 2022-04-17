College Football Analysis
==============================

![Project Logo](https://github.com/ereidelbach/Images/blob/master/CFB%20Logo.png?raw=true)

# Project Description

The overall goal of this project is to collect College Football data from a variety of sources on the web and to subsequently use it for a variety of analytical pursuits.

Project functions are written in a manner than will facilitate the continuous collection of data throughout a season (i.e. every week).

------------

# Links

1. ESPN CF Statistics: [Link][1]
2. NCAA Statistics: [Link][2]
3. CFB Stats: [Link][3]
4. Sports Reference: [Link][4]
5. USA Today Coaching Salaries [Link][5]
6. Betting Odds: [Link][6]
7. Team Colors: [Link][7]

  [1]: http://www.espn.com/college-football/statistics
  [2]: https://www.ncaa.com/stats/football/fbs
  [3]: http://www.cfbstats.com
  [4]: https://www.sports-reference.com/cfb/
  [5]: http://sports.usatoday.com/ncaa/salaries/
  [6]: http://www.drwagpicks.com/p/blog-page.html
  [7]: https://teamcolorcodes.com/premier-league-color-codes/


# Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
