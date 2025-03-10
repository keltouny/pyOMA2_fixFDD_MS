The ``ssi`` algorithm module
============================

This module implements the Stochastic Subspace Identification (SSI) [BPDG99]_, [MiDo11]_ algorithm in various forms,
tailored for both single and multiple experimental setup scenarios [MiDo11]_, [DOME13]_. It includes classes and methods
for conducting data-driven and covariance-driven SSI analyses, with optional uncertainty bounds estimation.

Classes:
   :class:`.SSIdat`
      Implements the Data-Driven SSI algorithm for single setup.
   :class:`.SSIcov`
      Implements the Covariance-Driven SSI algorithm for single setup.
   :class:`.SSIdat_MS`
      Extends ``SSIdat`` for multi-setup experiments.
   :class:`.SSIcov_MS`
      Extends ``SSIdat_MS`` for covariance-based analysis in multi-setup experiments.

.. Important::
   Each class contains methods for executing the SSI algorithm, extracting modal parameters,
   plotting results, and additional utilities relevant to the specific SSI approach.

.. Note::
   Users should be familiar with the concepts of modal analysis and system identification to effectively use this module.


The ``SSIdat`` class
-------------------------

.. autoclass:: pyoma2.algorithms.ssi.SSIdat
   :members:
   :inherited-members:
   :show-inheritance:

The ``SSIcov`` class
-------------------------

.. autoclass:: pyoma2.algorithms.ssi.SSIcov
   :members:
   :inherited-members:
   :show-inheritance:

The ``SSIdat_MS`` class
----------------------------

.. autoclass:: pyoma2.algorithms.ssi.SSIdat_MS
   :members:
   :inherited-members:
   :show-inheritance:


The ``SSIcov_MS`` class
----------------------------

.. autoclass:: pyoma2.algorithms.ssi.SSIcov_MS
   :members:
   :inherited-members:
   :show-inheritance:
