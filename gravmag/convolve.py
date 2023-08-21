"""
This file contains Python codes for dealing with 2D discrete convolutions.
"""

import numpy as np
from scipy.linalg import toeplitz, circulant
from scipy.fft import fft2, ifft2
from . import check


def compute(FT_data, filters, check_input=True):
    """
    Compute the convolution in Fourier domain as the Hadamard (or element-wise)
    product of the Fourier-Transformed data and a sequence of filters.

    parameters
    ----------
    FT_data : numpy array 2D
        Matrix obtained by computing the 2D Discrete Fourier Transform of a
        regular grid of potential-field data located on a horizontal plane.
    filter : list of numpy arrays 2D
        List of matrices having the same shape of FT_data. These matrices
        represent the sequence of filters to be applied in Fourier domain.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    convolved_data : numpy array 2D or flattened array 1D
        Convolved data as a grid or a flattened array 1D, depending on
        the parameter "grid".
    """

    if check_input is True:
        check.is_array(x=FT_data, ndim=2)
        shape_data = FT_data.shape
        if np.iscomplexobj(FT_data) == False:
            raise ValueError("FT_data must be a complex array")
        if type(filters) != list:
            raise ValueError("filters must be a list")
        if len(filters) == 0:
            raise ValueError("filters must have at least one element")
        for filter in filters:
            check.is_array(x=filter, ndim=2)
            shape_filter = filter.shape
            if shape_filter != shape_data:
                raise ValueError("filter must have the same shape as data")

    # create a single filter by multiplying all those
    # defined in filters
    resultant_filter = np.prod(filters, axis=0)

    # compute the convolved data in Fourier domain
    convolved_data = FT_data * resultant_filter

    return convolved_data


def generic_BTTB(
    symmetry_structure,
    symmetry_blocks,
    nblocks,
    columns,
    rows,
    check_input=True,
):
    """
    Generate a full Block Toeplitz formed by Toeplitz Blocks (BTTB)
    matrix T from the first columns and first rows of its non-repeating
    blocks.

    The matrix T has nblocks x nblocks blocks, each one with npoints_per_block x npoints_per_block elements.

    The first column and row of blocks forming the BTTB matrix T are
    represented as follows:

        |T11 T12 ... T1Q|
        |T21            |
    T = |.              | .
        |:              |
        |TQ1            |


    There are two symmetries:
    * symmetry_structure - between all blocks above and below the main block diagonal.
    * symmetry_blocks    - between all elements above and below the main diagonal within each block.
    Each symmetry pattern have three possible types:
    * gene - it denotes 'generic' and it means that there is no symmetry.
    * symm - it denotes 'symmetric' and it means that there is a perfect symmetry.
    * skew - it denotes 'skew-symmetric' and it means that the elements above the main diagonal
        have opposite signal with respect to those below the main diagonal.
    Hence, we consider that the BTTB matrix T has nine possible symmetry patterns:
    * 'symm-symm' - Symmetric Block Toeplitz formed by Symmetric Toeplitz Blocks
    * 'symm-skew' - Symmetric Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
    * 'symm-gene' - Symmetric Block Toeplitz formed by Generic Toeplitz Blocks
    * 'skew-symm' - Skew-Symmetric Block Toeplitz formed by Symmetric Toeplitz Blocks
    * 'skew-skew' - Skew-Symmetric Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
    * 'skew-gene' - Skew-Symmetric Block Toeplitz formed by Generic Toeplitz Blocks
    * 'gene-symm' - Generic Block Toeplitz formed by Symmetric Toeplitz Blocks
    * 'gene-skew' - Generic Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
    * 'gene-gene' - Generic Block Toeplitz formed by Generic Toeplitz Blocks

    parameters
    ----------
    symmetry_structure : string
        Defines the type of symmetry between all blocks above and below the main block diagonal.
        It can be 'gene', 'symm' or 'skew' (see the explanation above).
    symmetry_blocks : string
        Defines the type of symmetry between elements above and below the main diagonal within all blocks.
        It can be 'gene', 'symm' or 'skew' (see the explanation above).
    nblocks : int
        Number of blocks (nblocks) of T along column and row.
    columns : numpy array
        Matrix whose rows are the first columns cij of the non-repeating blocks
        Tij of T. They must be ordered as follows: c11, c21, ..., cQ1,
        c12, ..., c1Q.
    rows : None or numpy array 2D
        If not None, it is a matrix whose rows are the first rows rij of the
        non-repeating blocks Tij of T, without the diagonal term. They must
        be ordered as follows: r11, r21, ..., rM1, r12, ..., r1M.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    T: numpy array 2D
        The full BTTB matrix.
    """

    if check_input == True:
        check.BTTB_metadata(
            symmetry_structure, symmetry_blocks, nblocks, columns, rows
        )

    # number of points per block row/column
    npoints_per_block = columns.shape[1]
    # auxiliary variable used to create Toeplitz matrices
    # npoints_per_block = 4
    # ind_col_blocks =
    # [[0]
    #  [1]
    #  [2]
    #  [3]]
    # ind_row_blocks =
    # [[3 2 1 0]]
    # ind_blocks =
    # [[3 2 1 0]
    #  [4 3 2 1]
    #  [5 4 3 2]
    #  [6 5 4 3]]
    ind_col_blocks, ind_row_blocks = np.ogrid[
        0:npoints_per_block, npoints_per_block - 1 : -1 : -1
    ]
    ind_blocks = ind_col_blocks + ind_row_blocks

    if symmetry_structure == "symm":
        if symmetry_blocks == "symm":
            # 'symm-symm' - Symmetric Block Toeplitz formed by Symmetric Toeplitz Blocks
            blocks = []
            for column in columns:
                # create the block column in the correct order
                blocks.append(
                    # concatenate (i) row in reversed order and (ii) column in the correct order
                    # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                    np.concatenate((column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
        elif symmetry_blocks == "skew":
            # 'symm-skew' - Symmetric Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
            blocks = []
            for column in columns:
                # create the block column in the correct order
                blocks.append(
                    # concatenate (i) row in reversed order and (ii) column in the correct order
                    # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                    np.concatenate((-column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
        else:  # symmetry_blocks == 'gene'
            # 'symm-gene' - Symmetric Block Toeplitz formed by Generic Toeplitz Blocks
            blocks = []
            # create the block column in the correct order
            for column, row in zip(columns, rows):
                # concatenate (i) row in reversed order and (ii) column in the correct order
                # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                blocks.append(np.concatenate((row[::-1], column))[ind_blocks])
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
    elif symmetry_structure == "skew":
        if symmetry_blocks == "symm":
            # 'skew-symm' - Skew-Symmetric Block Toeplitz formed by Symmetric Toeplitz Blocks
            blocks = []
            for column in columns:
                # create the block column in the correct order
                blocks.append(
                    # concatenate (i) row in reversed order and (ii) column in the correct order
                    # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                    np.concatenate((column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (-np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
        elif symmetry_blocks == "skew":
            # 'skew-skew' - Skew-Symmetric Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
            blocks = []
            for column in columns:
                # create the block column in the correct order
                blocks.append(
                    # concatenate (i) row in reversed order and (ii) column in the correct order
                    # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                    np.concatenate((-column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (-np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
        else:  # symmetry_blocks == 'gene'
            # 'skew-gene' - Skew-Symmetric Block Toeplitz formed by Generic Toeplitz Blocks
            blocks = []
            # create the block column in the correct order
            for column, row in zip(columns, rows):
                # concatenate (i) row in reversed order and (ii) column in the correct order
                # create a matrix by indexing the concatenated vector with the auxiliary variable ind_blocks
                blocks.append(np.concatenate((row[::-1], column))[ind_blocks])
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (-np.stack(blocks)[-1:0:-1], np.stack(blocks))
            )
    else:  # symmetry_structure == 'gene'
        if symmetry_blocks == "symm":
            # 'gene-symm' - Generic Block Toeplitz formed by Symmetric Toeplitz Blocks
            blocks_1j = []
            # create the block column in the correct order
            for column in columns[:nblocks]:
                blocks_1j.append(
                    np.concatenate((column[-1:0:-1], column))[ind_blocks]
                )
            blocks_i1 = []
            # create the block row in the correct order
            for column in columns[nblocks:]:
                blocks_i1.append(
                    np.concatenate((column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks_i1)[::-1], np.stack(blocks_1j))
            )
        elif symmetry_blocks == "skew":
            # 'gene-skew' - Generic Block Toeplitz formed by Skew-Symmetric Toeplitz Blocks
            blocks_1j = []
            # create the block column in the correct order
            for column in columns[:nblocks]:
                blocks_1j.append(
                    np.concatenate((-column[-1:0:-1], column))[ind_blocks]
                )
            blocks_i1 = []
            # create the block row in the correct order
            for column in columns[nblocks:]:
                blocks_i1.append(
                    np.concatenate((-column[-1:0:-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks_i1)[::-1], np.stack(blocks_1j))
            )
        else:  # symmetry_blocks == 'gene'
            # 'gene-gene' - Generic Block Toeplitz formed by Generic Toeplitz Blocks
            blocks_1j = []
            # create the block column in the correct order
            for column, row in zip(columns[:nblocks], rows[:nblocks]):
                blocks_1j.append(
                    np.concatenate((row[::-1], column))[ind_blocks]
                )
            blocks_i1 = []
            # create the block row in the correct order
            for column, row in zip(columns[nblocks:], rows[nblocks:]):
                blocks_i1.append(
                    np.concatenate((row[::-1], column))[ind_blocks]
                )
            # concatenate (i) block row in reversed order and (ii) block column in the correct order
            concatenated_blocks = np.concatenate(
                (np.stack(blocks_i1)[::-1], np.stack(blocks_1j))
            )

    # auxiliary variable similar to ind_blocks
    ind_col, ind_row = np.ogrid[0:nblocks, nblocks - 1 : -1 : -1]
    indices = ind_col + ind_row

    # create the full BTTB matrix T by indexing the concatenated blocks
    # with the auxiliary variable indices
    T = np.hstack(np.hstack(concatenated_blocks[indices]))

    return T


def Circulant_from_Toeplitz(symmetry, column, row, full=True, check_input=True):
    """
    Generate the circulant Circulant matrix C which embbeds a Toeplitz matrix T.

    The Toeplitz matrix T has P x P elements. The embedding circulant matrix C has 2P x 2P elements.

    Matrix T is represented as follows:

        |t11 t12 ... t1P|
        |t21            |
    T = |.              | .
        |:              |
        |tP1            |


    We consider that matrix T may have three symmetry types:
    * gene - it denotes 'generic' and it means that there is no symmetry.
    * symm - it denotes 'symmetric' and it means that there is a perfect symmetry.
    * skew - it denotes 'skew-symmetric' and it means that the elements above the main diagonal
        have opposite signal with respect to those below the main diagonal.

    parameters
    ----------
    symmetry : string
        Defines the type of symmetry between elements above and below the main diagonal.
        It can be 'gene', 'symm' or 'skew' (see the explanation above).
    column : numpy array 1D
        First column of T.
    row : None or numpy array 1D
        If not None, it is the first row of T, without the diagonal element. In
        this case, T does not have the assumed symmetries (see the text above).
        If None, matrix T is symmetric or skew-symmetric. Default is None.
    full : boolean
        If True, returns the full BCCB matrix C. Otherwise, returns only its first column.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    C: numpy array 1D or 2D
        The full 2P x 2P circulant matrix or only its first column (see parameter 'full').
    """

    if check_input == True:
        check.Toeplitz_metadata(symmetry, column, row)
        if full not in [True, False]:
            raise ValueError("invalid parameter full ({})".format(full))

    # order of the Toeplitz matrix T
    P = column.size

    # define the first column of the BCCB matrix C by
    # concatenating (i) column in the correct order, (ii) a zero and (iii) row in the reversed order
    # 'row' is defined in terms of 'column' if symmetry is 'symm' or 'skew'
    if symmetry == "symm":
        C = np.hstack([column, 0, column[-1:0:-1]])
    elif symmetry == "skew":
        C = np.hstack([column, 0, -column[-1:0:-1]])
    else:  # symmetry == "gene"
        C = np.hstack([column, 0, row[::-1]])

    if full == True:
        # auxiliary variable used to create full Circulant matrices
        # P = 4
        # ind_col =
        # [[0]
        #  [1]
        #  [2]
        #  [3]
        #  [4]
        #  [5]
        #  [6]
        #  [7]]
        # ind_row =
        # [[ 0 -1 -2 -3 -4 -5 -6 -7]]
        # indices =
        # [[ 0 -1 -2 -3 -4 -5 -6 -7]
        #  [ 1  0 -1 -2 -3 -4 -5 -6]
        #  [ 2  1  0 -1 -2 -3 -4 -5]
        #  [ 3  2  1  0 -1 -2 -3 -4]
        #  [ 4  3  2  1  0 -1 -2 -3]
        #  [ 5  4  3  2  1  0 -1 -2]
        #  [ 6  5  4  3  2  1  0 -1]
        #  [ 7  6  5  4  3  2  1  0]]
        ind_col, ind_row = np.ogrid[0 : 2 * P, 0 : -2 * P : -1]
        indices = ind_col + ind_row
        return C[indices]
    else:  # full is False
        return C


# def BCCB_from_BTTB(symmetry_structure, symmetry_blocks, nblocks, columns, rows, rows=None):
#     """
#     Generate a circulant Block Circulant formed by Circulant Matrices (BCCB)
#     which embeds a Block Toeplitz formed by Toeplitz Blocks (BTTB) matrix T.

#     The matrix BTTB has nblocks x nblocks blocks, each one with npoints_per_block x npoints_per_block elements. The
#     embedding circulant matrix BCCB has 2Q x 2Q blocks, each one with 2P x 2P
#     elements.

#     The BCCB inherits the symmetry of BTTB matrix. It means that:

#     1) An arbitrary BTTB matrix produces an arbitrary BCCB matrix;
#     2) A Symmetric Block Toeplitz formed by Symmetric Toeplitz Blocks (SBTSTB)
#     produces a Symmetric Block Circulant formed by Symmetric Circulant Blocks
#     (SBCSCB);
#     3) A Block Toeplitz formed by Symmetric Toeplitz Blocks (BTSTB) produces a
#     Block Circulant formed by Symmetric Circulant Blocks (BCSCB);
#     4) A Symmetric Block Toeplitz formed by Toeplitz Blocks (SBTTB) produces a
#     Symmetric Block Circulant formed by Circulant Blocks (SBCCB).
#     For details, see function 'generic_BTTB'.

#     parameters
#     ----------
#     See function 'generic_BTTB' for a description of the input parameters.

#     returns
#     -------
#     C: numpy array 2D
#         BCCB matrix.
#     """

#     if check_input == True:
#         check.BTTB_metadata(symmetry_structure, symmetry_blocks, nblocks, columns, rows)

#     check.is_integer(x=nblocks, positive=True)
#     check.is_array(x=columns, ndim=2)
#     if (columns.shape[0] != nblocks) and (
#         columns.shape[0] != (2 * nblocks - 1)
#     ):
#         raise ValueError(
#             "the number of rows in 'columns' must be equal to 'nblocks' or equal to (2 * 'nblocks') - 1"
#         )

#     if rows is None:
#         T_npoints_per_block = columns.shape[1]
#         nonull_blocks = []
#         for column in columns:
#             nonull_blocks.append(Circulant_from_Toeplitz(column))
#         C_npoints_per_block = 2 * T_npoints_per_block

#         # Case SBTSTB
#         # The first block column of the BCCB matrix C is formed by stacking the
#         # first block column of the SBTSTB matrix T (nonull_blocks), a block
#         # with null elements and the reversed block column "nonull_blocks"
#         # without its first block. The first block of "nonull_blocks" lies on
#         # the main block diagonal of matrix T.
#         if columns.shape[0] == nblocks:
#             C_blocks = np.concatenate(
#                 (
#                     np.stack(nonull_blocks),
#                     np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
#                     np.stack(nonull_blocks[-1:0:-1]),
#                 )
#             )

#         # Case BTSTB
#         # The first block column of the BCCB matrix C is formed by stacking the
#         # first block column of the BTSTB matrix T (nonull_blocks[:nblocks]),
#         # a block with null elements and the reversed block row
#         # "nonull_blocks[-1:nblocks-1:-1]" without the block that lies on
#         # main block diagonal of matrix T.
#         if columns.shape[0] == (2 * nblocks - 1):
#             C_blocks = np.concatenate(
#                 (
#                     np.stack(nonull_blocks[:nblocks]),
#                     np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
#                     np.stack(nonull_blocks[-1 : nblocks - 1 : -1]),
#                 )
#             )

#     else:
#         check.is_array(x=rows, ndim=2)
#         if (columns.shape[0] != rows.shape[0]):
#             raise ValueError("the number of rows in 'rows' and 'columns' must be equal to each other")
#         if (columns.shape[1] != (rows.shape[1] + 1)):
#             raise ValueError("the number of columns in 'columns' must be equal that in 'rows' + 1")
#         T_npoints_per_block = columns.shape[1]
#         nonull_blocks = []
#         for column, rows in zip(columns, rows):
#             nonull_blocks.append(Circulant_from_Toeplitz(column, rows))
#         C_npoints_per_block = 2 * T_npoints_per_block

#         # Case SBTTB
#         # The first block column of the BCCB matrix C is formed by stacking the
#         # first block column of the SBTTB matrix T (nonull_blocks), a block
#         # with null elements and the reversed block column "nonull_blocks"
#         # without its first block. The first block of "nonull_blocks" lies on
#         # the main block diagonal of matrix T.
#         if columns.shape[0] == nblocks:
#             C_blocks = np.concatenate(
#                 (
#                     np.stack(nonull_blocks),
#                     np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
#                     np.stack(nonull_blocks[-1:0:-1]),
#                 )
#             )

#         # Case BTTB generalized
#         # The first block column of the BCCB matrix C is formed by stacking the
#         # first block column of the BTTB matrix T (nonull_blocks[:nblocks]),
#         # a block with null elements and the reversed block row
#         # "nonull_blocks[-1:nblocks-1:-1]" without the block that lies on
#         # main block diagonal of matrix T.
#         if columns.shape[0] == (2 * nblocks - 1):
#             C_blocks = np.concatenate(
#                 (
#                     np.stack(nonull_blocks[:nblocks]),
#                     np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
#                     np.stack(nonull_blocks[-1 : nblocks - 1 : -1]),
#                 )
#             )

#     nblocks_C = 2 * nblocks

#     ind_col, ind_row = np.ogrid[0:nblocks_C, 0:-nblocks_C:-1]
#     indices = ind_col + ind_row
#     C = np.hstack(np.hstack(C_blocks[indices]))

#     return C


def BCCB_from_BTTB(
    symmetry_structure,
    symmetry_blocks,
    nblocks,
    columns,
    rows,
    full=True,
    check_input=True,
):
    """
    Generate the circulant Block Circulant formed by Circulant Matrices (BCCB)
    which embeds a Block Toeplitz formed by Toeplitz Blocks (BTTB) matrix T.

    The matrix BTTB has nblocks x nblocks blocks, each one with npoints_per_block x npoints_per_block elements. The
    embedding circulant matrix BCCB has 2*nblocks x 2*nblocks blocks, each one with
    2*npoints_per_block x 2*npoints_per_block elements elements.

    The BCCB inherits the symmetries of its associated BTTB matrix. For details, see function 'generic_BTTB'.

    parameters
    ----------
    symmetry_structure, symmetry_blocks, nblocks, columns, rows
        See function 'generic_BTTB' for a description of the input parameters.
    full : boolean
        If True, returns the full BCCB matrix. Otherwise, returns only its first column.

    returns
    -------
    C: numpy array 1D or 2D
        The full BCCB matrix or only its first columns (see parameter 'full').
    """

    if check_input == True:
        check.BTTB_metadata(
            symmetry_structure, symmetry_blocks, nblocks, columns, rows
        )
        if full not in [True, False]:
            raise ValueError("invalid parameter full ({})".format(full))

    if rows is None:
        T_npoints_per_block = columns.shape[1]
        nonull_blocks = []
        for column in columns:
            nonull_blocks.append(Circulant_from_Toeplitz(column))
        C_npoints_per_block = 2 * T_npoints_per_block

        # Case SBTSTB
        # The first block column of the BCCB matrix C is formed by stacking the
        # first block column of the SBTSTB matrix T (nonull_blocks), a block
        # with null elements and the reversed block column "nonull_blocks"
        # without its first block. The first block of "nonull_blocks" lies on
        # the main block diagonal of matrix T.
        if columns.shape[0] == nblocks:
            C_blocks = np.concatenate(
                (
                    np.stack(nonull_blocks),
                    np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
                    np.stack(nonull_blocks[-1:0:-1]),
                )
            )

        # Case BTSTB
        # The first block column of the BCCB matrix C is formed by stacking the
        # first block column of the BTSTB matrix T (nonull_blocks[:nblocks]),
        # a block with null elements and the reversed block row
        # "nonull_blocks[-1:nblocks-1:-1]" without the block that lies on
        # main block diagonal of matrix T.
        if columns.shape[0] == (2 * nblocks - 1):
            C_blocks = np.concatenate(
                (
                    np.stack(nonull_blocks[:nblocks]),
                    np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
                    np.stack(nonull_blocks[-1 : nblocks - 1 : -1]),
                )
            )

    else:
        check.is_array(x=rows, ndim=2)
        if columns.shape[0] != rows.shape[0]:
            raise ValueError(
                "the number of rows in 'rows' and 'columns' must be equal to each other"
            )
        if columns.shape[1] != (rows.shape[1] + 1):
            raise ValueError(
                "the number of columns in 'columns' must be equal that in 'rows' + 1"
            )
        T_npoints_per_block = columns.shape[1]
        nonull_blocks = []
        for column, rows in zip(columns, rows):
            nonull_blocks.append(Circulant_from_Toeplitz(column, rows))
        C_npoints_per_block = 2 * T_npoints_per_block

        # Case SBTTB
        # The first block column of the BCCB matrix C is formed by stacking the
        # first block column of the SBTTB matrix T (nonull_blocks), a block
        # with null elements and the reversed block column "nonull_blocks"
        # without its first block. The first block of "nonull_blocks" lies on
        # the main block diagonal of matrix T.
        if columns.shape[0] == nblocks:
            C_blocks = np.concatenate(
                (
                    np.stack(nonull_blocks),
                    np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
                    np.stack(nonull_blocks[-1:0:-1]),
                )
            )

        # Case BTTB generalized
        # The first block column of the BCCB matrix C is formed by stacking the
        # first block column of the BTTB matrix T (nonull_blocks[:nblocks]),
        # a block with null elements and the reversed block row
        # "nonull_blocks[-1:nblocks-1:-1]" without the block that lies on
        # main block diagonal of matrix T.
        if columns.shape[0] == (2 * nblocks - 1):
            C_blocks = np.concatenate(
                (
                    np.stack(nonull_blocks[:nblocks]),
                    np.zeros((1, C_npoints_per_block, C_npoints_per_block)),
                    np.stack(nonull_blocks[-1 : nblocks - 1 : -1]),
                )
            )

    nblocks_C = 2 * nblocks

    ind_col, ind_row = np.ogrid[0:nblocks_C, 0:-nblocks_C:-1]
    indices = ind_col + ind_row
    C = np.hstack(np.hstack(C_blocks[indices]))

    return C


# try to use the same input as generic_BTTB(nblocks, columns, rows=None)
# the input above allows defining generic BTTB matrices and not only those
# with symmetry "skew-skew", "skew-symm", "symm-skew" or "symm-symm"


def embedding_BCCB_first_column(b0, nblocks, npoints_per_block, symmetry):
    """
    Compute the first column "c0" of the embedding BCCB matrix
    from the first column "b0" of a BTTB matrix.

    parameters
    ----------
    b0: numpy array 1d
        First column of the BTTB matrix.
    nblocks: int
        Number of blocks along a column/row of the BTTB.
    npoints_per_block: int
        Number of rows/columns of each block forming the BTTB.
    symmetry: string
        Define the symmetry of the BTTB matrix. We consider four types:
            "skew-skew" - skew-symmetric block Toeplitz formed by skew-symmetric Toeplitz blocks
            "skew-symm" - skew-symmetric block Toeplitz formed by symmetric Toeplitz blocks
            "symm-skew" - symmetric block Toeplitz formed by skew-symmetric Toeplitz blocks
            "symm-symm" - symmetric block Toeplitz formed by symmetric Toeplitz blocks

    returns
    -------
    BCCB0 : dictionary
        Contains all the information required to reconstruct the full originating BTTB
        matrix or the full BCCB matrix. The dictionary has the following keys:
        "first_column" : : numpy array 1d
            First column of the embedding BCCB matrix.
        "nblocks" : nblocks (input variable)
        "npoints_per_block" : npoints_per_block (input variable)
        "symmetry" : symmetry (input variable)


    """

    check.is_array(x=b0, ndim=1)
    check.is_integer(x=nblocks, positive=True)
    check.is_integer(x=npoints_per_block, positive=True)
    # check if b0 match nblocks and npoints_per_block
    if b0.size != nblocks * npoints_per_block:
        raise ValueError("b0 must have nblocks*npoints_per_block elements")
    # check if symmetry is valid
    if symmetry not in ["skew-skew", "skew-symm", "symm-skew", "symm-symm"]:
        raise ValueError("invalid {} symmetry".format(symmetry))

    # split b into nblocks parts
    b_parts = np.split(b0, nblocks)

    # define a list to store the pieces
    # of c0 that will be computed below
    c0 = []

    # define the elements of c0 for symmetry 'skew-skew'
    if symmetry == "skew-skew":
        # run the first block column of the BTTB
        for bi in b_parts:
            c0.append(np.hstack([bi, 0, -bi[:0:-1]]))
        # include zeros
        c0.append(np.zeros(2 * npoints_per_block))
        # run the first block row of the BTTB
        for bi in b_parts[:0:-1]:
            c0.append(np.hstack([-bi, 0, bi[:0:-1]]))

    # define the elements of c0 for symmetry 'skew-symm'
    if symmetry == "skew-symm":
        # run the first block column of the BTTB
        for bi in b_parts:
            c0.append(np.hstack([bi, 0, bi[:0:-1]]))
        # include zeros
        c0.append(np.zeros(2 * npoints_per_block))
        # run the first block row of the BTTB
        for bi in b_parts[:0:-1]:
            c0.append(np.hstack([-bi, 0, -bi[:0:-1]]))

    # define the elements of c0 for symmetry 'symm-skew'
    if symmetry == "symm-skew":
        # run the first block column of the BTTB
        for bi in b_parts:
            c0.append(np.hstack([bi, 0, -bi[:0:-1]]))
        # include zeros
        c0.append(np.zeros(2 * npoints_per_block))
        # run the first block row of the BTTB
        for bi in b_parts[:0:-1]:
            c0.append(np.hstack([bi, 0, -bi[:0:-1]]))

    # define the elements of c0 for symmetry 'symm-symm'
    if symmetry == "symm-symm":
        # run the first block column of the BTTB
        for bi in b_parts:
            c0.append(np.hstack([bi, 0, bi[:0:-1]]))
        # include zeros
        c0.append(np.zeros(2 * npoints_per_block))
        # run the first block row of the BTTB
        for bi in b_parts[:0:-1]:
            c0.append(np.hstack([bi, 0, bi[:0:-1]]))

    # concatenate c0 in a single vector
    c0 = np.concatenate(c0)

    # dictionary containing all metadata
    BCCB0 = {
        "first_column": c0,
        "nblocks": nblocks,
        "npoints_per_block": npoints_per_block,
        "symmetry": symmetry,
    }

    return BCCB0


def eigenvalues_BCCB(BCCB0, ordering="row"):
    """
    Compute the eigenvalues of a Block Circulant formed
    by Circulant Blocks (BCCB) matrix C. The eigenvalues
    are rearranged along the rows or columns of a matrix L.

    parameters
    ----------
    BCCB0 : dictionary
        See the definition at the function "embedding_BCCB_first_column".
    ordering: string
        If "row", the eigenvalues will be arranged along the rows of a matrix L;
        if "column", they will be arranged along the columns of a matrix L.

    returns
    -------
    BCCB_eigen : dictionary
        Contains all the metadata required to recontruct the first column or the
        full BCCB matrix. The dictionary has the following keys:
        "eigenvalues" : numpy array 2D
            Matrix formed by the eigenvalues of the BCCB.
        "ordering" : ordering (input variable)
        "nblocks" : nblocks (key forming the input dictionary BCCB0)
        "npoints_per_block" : npoints_per_block (key forming the input dictionary BCCB0)
        "symmetry" : string
            Define the symmetry of the BTTB matrix. We consider five types:
                "skew-skew" - skew-symmetric block Toeplitz formed by skew-symmetric Toeplitz blocks
                "skew-symm" - skew-symmetric block Toeplitz formed by symmetric Toeplitz blocks
                "symm-skew" - symmetric block Toeplitz formed by skew-symmetric Toeplitz blocks
                "symm-symm" - symmetric block Toeplitz formed by symmetric Toeplitz blocks
                "generic" - generic block Toeplitz formed by generic Toeplitz blocks
    """

    if type(BCCB0) != dict:
        raise ValueError("BCCB0 must be a dictionary")
    if list(BCCB0.keys()) != [
        "first_column",
        "nblocks",
        "npoints_per_block",
        "symmetry",
    ]:
        raise ValueError(
            "BCCB0 must have the following 4 keys: 'first_column', 'nblocks', 'npoints_per_block', 'symmetry'"
        )
    c0 = BCCB0["first_column"]
    nblocks = BCCB0["nblocks"]
    npoints_per_block = BCCB0["npoints_per_block"]
    symmetry = BCCB0["symmetry"]

    check.is_array(x=c0, ndim=1)
    check.is_integer(x=nblocks, positive=True)
    check.is_integer(x=npoints_per_block, positive=True)
    # check size of c0
    if c0.size != 4 * nblocks * npoints_per_block:
        raise ValueError("c0 must have 4*nblocks*npoints_per_block elements")
    # check if symmetry is valid
    if symmetry not in [
        "skew-skew",
        "skew-symm",
        "symm-skew",
        "symm-symm",
        "gene-symm",
        "symm-gene",
        "gene-skew",
        "skew-gene",
        "gene-gene",
    ]:
        raise ValueError("invalid {} symmetry".format(symmetry))
    # check if ordering is valid
    if ordering not in ["row", "column"]:
        raise ValueError("invalid {} ordering".format(ordering))

    # reshape c0 according to ordering
    if ordering == "row":
        # matrix containing the elements of c0 arranged along its rows
        G = np.reshape(c0, (2 * nblocks, 2 * npoints_per_block))
    else:  # if ordering == 'column':
        # matrix containing the elements of vector a arranged along its columns
        G = np.reshape(c0, (2 * nblocks, 2 * npoints_per_block)).T

    # compute the matrix L containing the eigenvalues
    L = np.sqrt(4 * nblocks * npoints_per_block) * fft2(x=G, norm="ortho")

    # dictionary containing all metadata
    BCCB_eigen = {
        "eigenvalues": L,
        "ordering": ordering,
        "nblocks": nblocks,
        "npoints_per_block": npoints_per_block,
        "symmetry": symmetry,
    }

    return BCCB_eigen


def transposition_factor(symmetry):
    """
    Define the transposition factor of an eigenvalues matrix
    (defined according to the function 'eigenvalues_BCCB') according to the symmetry
    (see the function 'embedding_BCCB_first_column') of its the originating BTTB matrix.
    """

    # check if symmetry is valid
    if symmetry not in ["skew-skew", "skew-symm", "symm-skew", "symm-symm"]:
        raise ValueError("invalid {} symmetry".format(symmetry))

    # define the transposition factor
    transposition_factor_dict = {
        "skew-skew": 1,
        "skew-symm": -1,
        "symm-skew": -1,
        "symm-symm": 1,
    }

    return transposition_factor_dict[symmetry]


def product_BCCB_vector(BCCB_eigen, v, check_input=True):
    """
    Compute the product of a BCCB matrix and a vector
    v by using the eigenvalues of the BCCB. This BCCB embeds
    a BTTB matrix formed by nblocks x nblocks blocks, each one with
    npoints_per_block x npoints_per_block elements.

    parameters
    ----------
    BCCB_eigen : dictionary
        See the definition at the function "eigenvalues_BCCB"
    v: numpy array 1d
        Vector to be multiplied by the BCCB matrix.
    check_input : boolean
        If True, verify if the input is valid. Default is True.

    returns
    -------
    w: numpy array 1d
        Vector containing the non-null elements of the product of the BCCB
        matrix and vector v.
    """

    if check_input == True:
        if type(BCCB_eigen) != dict:
            raise ValueError("BCCB_eigen must be a dictionary")
        if list(BCCB_eigen.keys()) != [
            "eigenvalues",
            "ordering",
            "nblocks",
            "npoints_per_block",
            "symmetry",
        ]:
            raise ValueError(
                "BCCB0 must have the following 5 keys: 'eigenvalues', 'ordering', 'nblocks', 'npoints_per_block', 'symmetry'"
            )

        L = BCCB_eigen["eigenvalues"]
        ordering = BCCB_eigen["ordering"]
        nblocks = BCCB_eigen["nblocks"]
        npoints_per_block = BCCB_eigen["npoints_per_block"]
        symmetry = BCCB_eigen["symmetry"]

        if ordering not in ["row", "column"]:
            raise ValueError("invalid ordering {}".format(ordering))

        check.is_integer(x=nblocks, positive=True)
        check.is_integer(x=npoints_per_block, positive=True)

        if ordering == "row":
            check.is_array(
                x=L, ndim=2, shape=(2 * nblocks, 2 * npoints_per_block)
            )
        else:  # if ordering == 'column':
            check.is_array(
                x=L, ndim=2, shape=(2 * npoints_per_block, 2 * nblocks)
            )

        check.is_array(x=v, ndim=1, shape=(nblocks * npoints_per_block,))

    if ordering == "row":
        # matrix containing the elements of vector a arranged along its rows
        V = np.reshape(v, (nblocks, npoints_per_block))
        V = np.hstack([V, np.zeros((nblocks, npoints_per_block))])
        V = np.vstack([V, np.zeros((nblocks, 2 * npoints_per_block))])
    else:  # if ordering == 'column':
        # matrix containing the elements of vector a arranged along its columns
        V = np.reshape(v, (nblocks, npoints_per_block)).T
        V = np.hstack([V, np.zeros((npoints_per_block, nblocks))])
        V = np.vstack([V, np.zeros((npoints_per_block, 2 * nblocks))])

    # matrix obtained by computing the Hadamard product
    H = L * fft2(x=V, norm="ortho")

    # matrix containing the non-null elements of the product BCCB v
    # arranged according to the parameter 'ordering'
    # the non-null elements are located in the first quadrant.
    if ordering == "row":
        w = ifft2(x=H, norm="ortho")[:nblocks, :npoints_per_block].real
        w = w.ravel()
    else:  # if ordering == 'column':
        w = ifft2(x=H, norm="ortho")[:npoints_per_block, :nblocks].real
        w = w.T.ravel()

    return w


# def eigenvalues_matrix(h_hat, u_hat, eigenvalues_K,
#                        N_blocks, N_points_per_block):
#     '''
#     Compute the eigenvalues matrix L of the "u_hat" magnetic field component
#     produced by a dipole layer with magnetization direction "h_hat".
#     '''
#     f0 = h_hat[0]*u_hat[0] - h_hat[2]*u_hat[2]
#     f1 = h_hat[0]*u_hat[1] + h_hat[1]*u_hat[0]
#     f2 = h_hat[0]*u_hat[2] + h_hat[2]*u_hat[0]
#     f3 = h_hat[1]*u_hat[1] - h_hat[2]*u_hat[2]
#     f4 = h_hat[1]*u_hat[2] + h_hat[2]*u_hat[1]
#     factors = [f0, f1, f2, f3, f4]
#
#     L = np.zeros((2*N_blocks, 2*N_points_per_block), dtype='complex')
#
#     for factor, eigenvalues_Ki in zip(factors, eigenvalues_K):
#
#         # compute the matrix of eigenvalues of the embedding BCCB
#         L += factor*eigenvalues_Ki
#
#     L *= cts.CMT2NT
#
#     return L


# def H_matrix(y, n):
#     '''
#     Matrix of the Fourier series model for producing
#     the annihilator model.
#
#     parameters
#     ----------
#     y: numpy array 2D
#         Rotated coordinate y computed with function
#         "utils.coordinate_transform".
#     n: int
#         Positive integer defining the maximum degree of the Fourier series
#         model.
#
#     returns
#     -------
#     H: numpy array 2D
#         Matrix of the Fourier series model.
#     '''
#     assert (isinstance(n, int)) and (n > 0), 'n must be a positive integer'
#     shapey = y.shape
#     L = np.max(y) - np.min((y))
#     arg = 2*np.pi*np.outer(y.ravel(), np.arange(n+1))/L
#     H = np.hstack([np.cos(arg), np.sin(arg)])
#     return H
