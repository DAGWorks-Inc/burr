==========
Installing
==========

Burr requires almost no dependencies. Every "extra"/"plugin" is an additional install target. Note, if you're using ``zsh``,
you'll need to add quotes around the install target, like `pip install "burr[graphviz]"`.

.. code-block:: bash

    pip install burr

To get visualization capabilities, you can install the `burr[graphviz]` extra:

.. code-block:: bash

    pip install burr[graphviz]

And to visualize your state machines on streamlit, you can install the `burr[streamlit]` extra:

.. code-block:: bash

    pip install burr[streamlit]

Don't worry, you can always install these extras later if you need them.
