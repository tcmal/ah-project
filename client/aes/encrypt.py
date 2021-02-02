import numpy as np
from aes.key_extension import extend_key, createRoundKey
from aes.common import get_blocks, KEY_SIZE, addRoundKey, shiftRows, sbox, mixColumns

def encrypt(msg, key):
    # Sanity check
    assert len(key) == KEY_SIZE

    # Divide data into blocks
    blocks = get_blocks(msg)

    # Derive a series of other keys
    extended_keys = extend_key(key)

    # Encrypt each block with 14 rounds
    ## For each block of data
    for i in range(0, len(blocks)):
        ## Encrypt with 14 rounds
        blocks[i] = encrypt_block(blocks[i], extended_keys)

    # Return the ciphertext flattened to a bytearray
    return bytearray(list(np.array([x.flatten(order='F') for x in blocks]).flatten()))

def encrypt_block(block, extended_keys):
    # Add the first key to start
    block = addRoundKey(block, createRoundKey(extended_keys, 0))

    # For round 1 -> 14
    for round_ in range(1, 14):
        # Get the key for this round
        round_key = createRoundKey(extended_keys, round_)

        # Perform one round of encryption
        block = aes_round(block, round_key)

    # Some final operations
    block = sbox(block)
    block = shiftRows(block)
    block = addRoundKey(block, createRoundKey(extended_keys, 14))

    return block


def aes_round(block, round_key):
    # Substitute each byte in the block according to the S-Box
    block = sbox(block)

    # Circular shift each row of the matrix
    block = shiftRows(block)

    # Mix up each column of the matrix
    block = mixColumns(block)

    # XOR the block with the key
    block = addRoundKey(block, round_key)
    return block
