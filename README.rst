########
Overview
########

This NApp is responsible for data persistence, saving and retrieving
information. It can be acessed by external agents through the REST API or by
other NApps, using the event-based methods.

Each box of data can be saved in a different namespace, with support for nested
namespaces.

The NApp is designed to support many options of back-end persistence solutions.
Currently it features filesystem operations, but alternatives such as SQL or
NoSQL databases will be implemented.

##########
Installing
##########

All of the Kytos Network Applications are located in the NApps online
repository. To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/storehouse

######
Events
######

********
Listened
********

The NApp listens to events requesting operations. Every event must have a
callback function to be executed right after the internal method returns. The
signature of the callback function is described with each event.

kytos.storehouse.create
=======================
Event requesting to save data to a box in a namespace.

Content
-------

.. code-block:: python3

   {
       data: <any data to be saved>,
       namespace: <namespace name>,
       callback: <callback function> # To be executed after the method returns.
   }

Callback function
-----------------

.. code-block:: python3

   def callback_function_name(box, error=False):
       # box: copy of the Box instance stored with data and metadata.
       # error: False when the operation is successful, True otherwise.

kytos.storehouse.retrieve
=========================
Event requesting to load data from a box in a namespace.

Content
-------

.. code-block:: python3

   {
       box_id: <ID of the Box to retrieve data from>,
       namespace: <namespace name>,
       callback: <callback function> # To be executed after the method returns.
   }

Callback function
-----------------

.. code-block:: python3

   def callback_function_name(box, error=False):
       # box: the retrieved Box instance.
       # error: False when the operation is successful, True otherwise.

kytos.storehouse.list
=====================
Event requesting to list all boxes in a namespace.

Content
-------

.. code-block:: python3

   {
       namespace: <namespace name>,
       callback: <callback function> # To be executed after the method returns.
   }

Callback function
-----------------

.. code-block:: python3

   def callback_function_name(box_list, error=False):
       # box_list: the retrieved list of Box.box_id.
       # error: False when the operation is successful, True otherwise.

kytos.storehouse.delete
=======================
Event requesting to remove a box from a namespace.

Content
-------

.. code-block:: python3

   {
       box_id: <ID of the Box to be deleted>,
       namespace: <namespace name>,
       callback: <callback function> # To be executed after the method returns.
   }

Callback function
-----------------

.. code-block:: python3

   def callback_function_name(result, error=False):
       # result: True if the box was deleted, False otherwise .
       # error: False when the operation is successful, True otherwise.


########
Rest API
########

You can find a list of the available endpoints and example input/output in the
'REST API' tab in this NApp's webpage in the `Kytos NApps Server
<https://napps.kytos.io/kytos/storehouse>`_.
