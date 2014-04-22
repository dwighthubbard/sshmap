
Submitting bugs
===============

Due diligence
-------------

Before submitting a bug, please do the following:

* Perform **basic troubleshooting** steps:

    * **Make sure you're on the latest version.** If you're not on the most
      recent version, your problem may have been solved already! Upgrading is
      always the best first step.
    * **Try older versions.** If you're already *on* the latest release, try
      rolling back a few minor versions (e.g. if on 1.7, try 1.5 or 1.6) and
      see if the problem goes away. This will help the devs narrow down when
      the problem first arose in the commit log.
    * **Try switching up dependency versions.** If the software in question has
      dependencies (other libraries, etc) try upgrading/downgrading those as
      well.

* **Search the project's bug/issue tracker** to make sure it's not a known
  issue.
* If you don't find a pre-existing issue, consider **checking with the mailing
  list and/or IRC channel** in case the problem is non-bug-related.

What to put in your bug report
------------------------------

Make sure your report gets the attention it deserves: bug reports with missing
information may be ignored or punted back to you, delaying a fix.  The below
constitutes a bare minimum; more info is almost always better:

* **What version of the core programming language interpreter/compiler are you
  using?** For example, if it's a Python project, are you using Python 2.7.3?
  Python 3.3.1? PyPy 2.0?
* **What operating system are you on?** Windows? (Vista? 7? 32-bit? 64-bit?)
  Mac OS X?  (10.7.4? 10.9.0?) Linux? (Which distro? Which version of that
  distro? 32 or 64 bits?) Again, more detail is better.
* **Which version or versions of the software are you using?** Ideally, you
  followed the advice above and have ruled out (or verified that the problem
  exists in) a few different versions.
* **How can the developers recreate the bug on their end?** If possible,
  include a copy of your code, the command you used to invoke it, and the full
  output of your run (if applicable.)

    * A common tactic is to pare down your code until a simple (but still
      bug-causing) "base case" remains. Not only can this help you identify
      problems which aren't real bugs, but it means the developer can get to
      fixing the bug faster.


Contributing changes
====================

Version control branching
-------------------------

* Always **make a new branch** for your work, no matter how small. This makes
  it easy for others to take just that one set of changes from your repository,
  in case you have multiple unrelated changes floating around.

    * A corollary: **don't submit unrelated changes in the same branch/pull
      request**! The maintainer shouldn't have to reject your awesome bugfix
      because the feature you put in with it needs more review.

* **Base your new branch off of the appropriate branch** on the main
  repository:

    * **Bug fixes** should be based on the branch named after the **oldest
      supported release line** the bug affects.

        * E.g. if a feature was introduced in 1.1, the latest release line is
          1.3, and a bug is found in that feature - make your branch based on
          1.1.  The maintainer will then forward-port it to 1.3 and master.
        * Bug fixes requiring large changes to the code or which have a chance
          of being otherwise disruptive, may need to base off of **master**
          instead. This is a judgement call -- ask the devs!

    * **New features** should branch off of **the 'master' branch**.

        * Note that depending on how long it takes for the dev team to merge
          your patch, the copy of ``master`` you worked off of may get out of
          date! If you find yourself 'bumping' a pull request that's been
          sidelined for a while, **make sure you rebase or merge to latest
          master** before generating the pull request to ensure a speedier
          resolution.

Code formatting
---------------

Code contributions should be formatted in compliance with
`PEP-8 <http://www.python.org/dev/peps/pep-0008/>` guidelines.

This is critically important because formatting changes can make pull requests
larger and harder to evalute.  Therefore not using PEP8 formating can cause
your change to be rejected.


Documentation isn't optional
----------------------------

It's not! Patches without documentation will be returned to sender.  By
"documentation" we mean:

* **Docstrings** (This step is optional for some bugfixes.)

* All submissions should have a **changelog entry** crediting the contributor
  and/or any individuals instrumental in identifying the problem.

Tests aren't optional
---------------------


Any bugfix that doesn't include a test proving the existence of the bug being
fixed, may be suspect.  Ditto for new features that can't prove they actually
work.

We've found that test-first development really helps make features better
architected and identifies potential edge cases earlier instead of later.
Writing tests before the implementation is strongly encouraged.


Pre-Submission checks
---------------------
It is highly recommended that before submitting a change the following can
be completed sucessfully:
  * The PEP8 tool runs and shows no new errors or warnings against the changed
    code.
  * The PyLint tool runs and shows new new errors against the changed code.  In
    the event the pylint tool shows a false positive warning or error, make sure
    the information about the pylint issue and why it is not an issue are
    documented inline inside the code.

