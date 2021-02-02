import numpy as np
from aes.key_extension import extend_key, createRoundKey
from aes.common import get_blocks, KEY_SIZE, addRoundKey, shiftRows, sbox, mixColumns

def decrypt(msg, key):
    # Sanity check
    assert len(key) == KEY_SIZE

    # Divide data into blocks
    blocks = get_blocks(msg)

    # Derive a series of other keys
    extended_keys = extend_key(key)

    # Decrypt each block
    ## For each block of data
    for i in range(0, len(blocks)):
        ## Decrypt
        blocks[i] = decrypt_block(blocks[i], extended_keys)

    return np.array([x.flatten(order='F') for x in blocks]).flatten()

def decrypt_block(block, extended_keys):
    # Reverse the final operations
    block = addRoundKey(block, createRoundKey(extended_keys, 14))
    block = shiftRows(block, True)
    block = sbox(block, True)
    
    # For round 14 -> 1
    for round_ in range(13, 0, -1):
        # Get the key for this round
        round_key = createRoundKey(extended_keys, round_)

        # Decrypt this round
        block = aes_decrypt_round(block, round_key)

    # Finally, reverse the first key
    # In this case, adding is its own inverse
    block = addRoundKey(block, createRoundKey(extended_keys, 0))
    return block

def aes_decrypt_round(block, round_key):
    # XOR the block with the key
    block = addRoundKey(block, round_key)

    # Mix up each column of the matrix
    block = mixColumns(block, True)

    # Circular shift each row of the matrix
    block = shiftRows(block, True)
    
    # Substitute each byte in the block according to the S-Box
    block = sbox(block, True)
    
    return block
