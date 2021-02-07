# Tadpoles Downloader

Patrick Wagstrom &lt;patrick@wagstrom.net&gt;

February 2021

This script was created because the daycare center we use was switching from Tadpoles to another system for storing information about each child's day, including photos. I started some of this years ago, but it was really out of date.

Normally this task would be pretty straight forward, but Tadpoles does a lot of things to try to actively thwart mass downloading of photos. However, we can script a headless Chrome browser to do whatever we want. Basically, if the image gets sent to the browser, we can save it.

## Getting Started

I used Conda to manage all of the dependencies necessary for this tool. The complete environment from my Mac is in `environment.yml`. If you're on a different platform, you may want to try `environment_history.yml`, which contains only the explicitly requested packages (note: it appears this misses some things like `pip install webdriver-manager`).

To restore the environment run:

```bash
conda env create -f environment.yml
```

## Running the Script

1. Activate the environment using `conda activate tadpoles2`

2. Open the notebook by running `jupyter notebook tadpoles.ipynb`

3. Edit the second code cell to set `TADPOLES_USERNAME` and `TADPOLES_PASSWORD`.

4. Create the directory mentioned in the second code cell for downloads (this defaults to something called `intermediate`).

5. From here, you should be able to just run the notebook and it _should_ start downloading all of the photos.

## Caveats

This a really hacky way to get at everything. I tried to keep most things done with Selenium looking at the XPath - even though a few elements might've been easier by injecting client scripts to look at the browser variables. I'm sure it will probably break in a couple of weeks or when someone with a child other than mine tries to use the script.