# Dragon's Dogma Wiki Parser

I found myself wanting to generate large tables of the contents of the [Dragon's Dogma wiki](http://dragonsdogma.wikia.com), so I wrote a script to scrape it, and then generate those tables.

## Dependencies

* Python 3.5+ (maybe earlier versions will work, but I've only tested with 3.5.)
* The [requests](http://docs.python-requests.org/) Python library.
** `pip install requests`

## downloader.py

`python downloader.py [page name]`

This script gets a listing of all of the equipment pages, and then extracts the wiki markup for each page, saving it into a file in the 'cache' directory under the current directory.

If a page name is given, only that page is downloaded. This is useful for refreshing your cache after editing a page.

## parse_equipment.py

`python parse_equipment.py <category>`

After downloading all of the pages with `downloader.py`, we can extract the template data for each item, and then generate tables for each item level, and group them together within `<tabber></tabber>` tags. Prints the result to stdout.

The category matches the wiki category for a class of equipment: Swords, Shields, Torso Armor, etc.