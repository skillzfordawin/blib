#   Manul - AFL helper
#   -------------------------------------
#   Maksim Shudrak <mshudrak@salesforce.com> <mxmssh@gmail.com>
#
#   Copyright 2019 Salesforce.com, inc. All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import random
import os

AFL_MAX_FILE = 1 << 15

# Extra-large blocks, selected very rarely (<5% of the time): */
AFL_HAVOC_BLK_XL = 32768
# Caps on block sizes
AFL_HAVOC_BLK_SMALL = 32
AFL_HAVOC_BLK_MEDIUM = 128
AFL_HAVOC_BLK_LARGE = 1500

AFL_ARITH_MAX = 35
AFL_HAVOC_STACK_POW2 = 7
SPLICE_CYCLES = 15
AFL_HAVOC_CYCLES = 256
AFL_HAVOC_MAX_MULT = 16
AFL_SPLICE_HAVOC = 32

#TODO: check in AFL
interesting_8_Bit = [128, 255, 0, 1, 16, 32, 64, 100, 127]
interesting_16_Bit = [65535, 32897, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
interesting_32_Bit = [4294967295, 2248146693, 2147516417, 32768, 65535, 65536, 100663045, 2147483647]

random.seed(os.urandom(4))

def locate_diffs(data1, data2):
	f_loc = -1
	l_loc = -1

	length = MIN(len(data1), len(data2))
	
	for i in range(0, length):
		if data1[i] != data2[i]:
			if f_loc == -1:
				f_loc = i
			l_loc = i
	return f_loc, l_loc


def AFL_choose_block_len(limit):
	# Caps on block sizes for cloning and deletion operations. Each of these
	# ranges has a 33% probability of getting picked, except for the first
	# two cycles where smaller blocks are favored.
	# TODO: in afl they have this: MIN(queue_cycle, 3)
	rlim = 3

	#TODO: afl has this
	#if not run_over10m:
		#rlim = 1

	case_id = RAND(rlim)
	if case_id == 0:
		min_value = 1
		max_value = AFL_HAVOC_BLK_SMALL
	elif case_id == 1:
		min_value = AFL_HAVOC_BLK_SMALL
		max_value = AFL_HAVOC_BLK_MEDIUM
	else:
		case_id = RAND(10)
		if case_id:
			min_value = AFL_HAVOC_BLK_MEDIUM
			max_value = AFL_HAVOC_BLK_LARGE
		else:
			min_value = AFL_HAVOC_BLK_LARGE
			max_value = AFL_HAVOC_BLK_XL

	if min_value >= limit:
		min_value = 1

	return min_value + RAND(MIN(max_value, limit) - min_value + 1)

def MIN(value_a, value_b):
	if value_a > value_b:
		return value_b
	else:
		return value_a

def reseed():
	random.seed(os.urandom(4))

def RAND(value):
	if value == 0:
		return value
	return random.randint(0, value-1)

def load_8(value, pos):
	return value[pos]


def load_16(value, pos):
	return (value[pos] << 8) + (value[pos+1] % 0xff)


def load_32(value, pos):
	return (value[pos] << 24) + (value[pos+1] << 16) + (value[pos+2] << 8) + (value[pos+3] % 0xff)


def store_8(data, pos, value):
	data[pos] = in_range_8(value)


def store_16(data, pos, value):
	value = in_range_16(value)
	data[pos]   = (value & 0xff00) >> 8
	data[pos+1] = (value & 0x00ff)


def store_32(data, pos, value):
	value = in_range_32(value)
	data[pos]   = (value & 0xff000000) >> 24
	data[pos+1] = (value & 0x00ff0000) >> 16
	data[pos+2] = (value & 0x0000ff00) >> 8
	data[pos+3] = (value & 0x000000ff)


def in_range_8(value):
	return value & 0xff


def in_range_16(value):
	return value & 0xffff


def in_range_32(value):
	return value & 0xffffffff


def swap_16(value):
	return (((value & 0xff00) >> 8) +
			((value & 0xff) << 8))


def swap_32(value):
	return ((value & 0x000000ff) << 24) + \
		   ((value & 0x0000ff00) << 8) + \
		   ((value & 0x00ff0000) >> 8) + \
		   ((value & 0xff000000) >> 24)


def bytes_to_str_8(value):
	return chr((value & 0xff))


def bytes_to_str_16(value):
	return chr((value & 0xff00) >> 8) + \
		   chr((value & 0x00ff))


def bytes_to_str_32(value):
	return chr((value & 0xff000000) >> 24) + \
		   chr((value & 0x00ff0000) >> 16) + \
		   chr((value & 0x0000ff00) >> 8) + \
		   chr((value & 0x000000ff))


def to_string_16(value):
	return chr((value >> 8) & 0xff) + \
		   chr(value & 0xff)


def to_string_32(value):
	return chr((value >> 24) & 0xff) + \
		   chr((value >> 16) & 0xff) + \
		   chr((value >> 8) & 0xff) + \
		   chr(value & 0xff)


def is_not_bitflip(value):
	return True
	if value == 0:
		return False

	sh = 0
	while (value & 1) == 0:
		sh += 1
		value >>= 1

	if value == 1 or value == 3 or value == 15:
		return False

	if (sh & 7) != 0:
		return True

	if value == 0xff or value == 0xffff or value == 0xffffffff:
		return False

	return True


def is_not_arithmetic(value, new_value, num_bytes, set_arith_max=None):
	if value == new_value:
		return False

	if not set_arith_max:
		set_arith_max = AFL_ARITH_MAX

	diffs = 0
	ov = 0
	nv = 0
	for i in range(num_bytes):
		a = value >> (8 * i)
		b = new_value >> (8 * i)
		if a != b:
			diffs += 1
			ov = a
			nv = b

	if diffs == 1:
		if in_range_8(ov - nv) <= set_arith_max or in_range_8(nv-ov) <= set_arith_max:
			return False

	if num_bytes == 1:
		return True

	diffs = 0
	for i in range(num_bytes / 2):
		a = value >> (16 * i)
		b = new_value >> (16 * i)

		if a != b:
			diffs += 1
			ov = a
			nv = b

	if diffs == 1:
		if in_range_16(ov - nv) <= set_arith_max or in_range_16(nv - ov) <= set_arith_max:
			return False

		ov = swap_16(ov)
		nv = swap_16(nv)

		if in_range_16(ov - nv) <= set_arith_max or in_range_16(nv - ov) <= set_arith_max:
			return False

	if num_bytes == 4:
		if in_range_32(value - new_value) <= set_arith_max or in_range_32(new_value - value) <= set_arith_max:
			return False

		value = swap_32(value)
		new_value = swap_32(new_value)

		if in_range_32(value - new_value) <= set_arith_max or in_range_32(new_value - value) <= set_arith_max:
			return False

	return True


def is_not_interesting(value, new_value, num_bytes, le):
	if value == new_value:
		return False

	for i in range(num_bytes):
		for j in range(len(interesting_8_Bit)):
			tval = (value & ~(0xff << (i * 8))) | (interesting_8_Bit[j] << (i * 8))
			if new_value == tval:
				return False

	if num_bytes == 2 and not le:
		return True

	for i in range(num_bytes - 1):
		for j in range(len(interesting_16_Bit)):
			tval = (value & ~(0xffff << (i * 8)) | (interesting_16_Bit[j] << (i * 8)))
			#print(" -> " + str(value) + " - " + str(new_value) + " - " + str(tval))
			if new_value == tval:
				return False

			#if num_bytes > 2:
			tval = (value & ~(0xffff << (i * 8))) | (swap_16(interesting_16_Bit[j]) << (i * 8));
			if new_value == tval:
				return False

	if num_bytes == 4 and le:
		for j in range(len(interesting_32_Bit)):
			if new_value == interesting_32_Bit[j]:
				return False

	return True

def cut(buf, skip_at, skip_len):
	return buf[:skip_at] + buf[skip_at+skip_len:]