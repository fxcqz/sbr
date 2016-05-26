Static Site Generator
=====================

Generate my personal site with some crappy python code, I would rather it be in
another programming language purely for my own learning experience but this
works as a good prototype.

Features
--------
 - custom file format for posts with flexible metadata, arbitrary variables can
   be used (currently all parsed as strings)
 - post content parsed as rst
 - no overhead so making changes to old posts is as simple as regenerating

How it works
------------

Posts are parsed from the posts dir (by default: ``_posts/``) and output as
their own static html files as well as being indexed on any page with the
``{{ posts }}`` templatetag.

The structure of the site directory (by default ``_site/``) is copied to the
output dir during generation with the same structure except there will be
additional post files in the output.

Pages can be skipped by providing a ``{{ static }}`` tag in the source (site)
file. These will still substitute globals.
