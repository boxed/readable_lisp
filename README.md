Readable Lisp
=============

An implementation of a subset of the Readable Lisp Project ( http://readable.sourceforge.net/ ). 
Currently only supports Clojure and just the indent-instead-of-parenthesis part of the Readable Lisp spec. 
Even those parts are probably rather buggy :P

Example:

```clojure
ns timelike.node
    :refer-clojure
        :exclude
        [time future]
    :import
        java.util.concurrent
            ConcurrentSkipListSet
            CountDownLatch
            LinkedBlockingQueue
            LinkedTransferQueue
            TimeUnit
    :use
        timelike.scheduler
        clojure.math.numeric-tower
        [incanter.distributions :only [draw exponential-distribution]]
```

is turned into this (although not pretty-printed like this):

```clojure
(ns timelike.node
    (:refer-clojure
        :exclude
        [time future])
    (:import
        (java.util.concurrent
            ConcurrentSkipListSet
            CountDownLatch
            LinkedBlockingQueue
            LinkedTransferQueue
            TimeUnit))
    (:use
        timelike.scheduler
        clojure.math.numeric-tower
        [incanter.distributions :only [draw exponential-distribution]]))
```

Usage
=====

```untab test.clj-readable``` 

will output standard Clojure source code for the file test.clj-readable

Rationale
=========

I wrote this because I wanted to play around with the concept of Readable Lisp but 
getting that project to build on my machine took me a long time and at the end I 
couldn't even get it to work. Then I found the Parsley library which seemed to make
it a bit easier to write parsers so I thought I'd give it a shot since I've never 
played with parser libraries before :P
