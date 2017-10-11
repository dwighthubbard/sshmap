sshmap 
******

.. image:: https://travis-ci.org/yahoo/sshmap.svg
    :target: https://travis-ci.org/yahoo/sshmap
    
Description
===========

sshmap is a python scriptable ssh multiplexer optimized for performing 
parallel map operations via ssh.

It has the following features:

* Rapidly run a single command or script on one or multiple hosts
* Scalable, a single host can run operate on very large numbers of systems
* Supports async callbacks
* Streams and executes commands to remote systems without writing them
  to disk on the remote systems.
* Jupyter/IPython notebook features

Provides Multiple interfaces:

* Provides Python classes for running commands on multiple systems.
* Command line utility
* Jupyter/IPython notebook extension

Dependencies
============

sshmap uses two open source modules.

This file summarizes the tools used, their purpose, and the licenses under
which they're released.

paramiko (LGPL license)
+++++++++++++++++++++++

This is a python module for making SSH2 connections (client or server). 
Emphasis is on using SSH2 as an alternative to SSL for making secure 
connections between python scripts. All major ciphers and hash methods 
are supported.  SFTP client and server mode are both supported too.

[http://www.lag.net/paramiko/]

hostlists (Apache License)
++++++++++++++++++++++++++

This is a python module for querying and managing lists of hosts from
various systems.

[https://github.com/yahoo/hostlists]
