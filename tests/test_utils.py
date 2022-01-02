# import pytest

# from utils import Bucket, PriorityQueue, clamp, int_to_ordinal, int_to_roman, roman_to_int


# def test_bucket():
#     bucket: Bucket[int] = Bucket(5)

#     assert bucket.capacity == 5
#     assert bucket.full == False
#     assert len(bucket) == 0

#     bucket.add(42)
#     bucket.add(23)
#     bucket.add(35)

#     assert bucket.full == False
#     assert len(bucket) == 3

#     bucket.add(37)
#     bucket.add(61)

#     assert bucket.full == True
#     assert len(bucket) == 5

#     with pytest.raises(RuntimeError):
#         bucket.add(0)


# def test_priority_queue():
#     pq: PriorityQueue[str] = PriorityQueue()

#     assert len(pq) == 0
#     assert pq.is_empty == True

#     pq.push(2, "James")
#     pq.push(0, "Alice")
#     pq.push(1, "Chris")
#     pq.push(0, "Salazar")

#     assert len(pq) == 4
#     assert pq.is_empty == False

#     assert pq.pop() == "Alice"
#     assert pq.pop() == "Salazar"

#     assert len(pq) == 2

#     assert pq.pop() == "Chris"
#     assert pq.pop() == "James"

#     assert len(pq) == 0
#     assert pq.is_empty == True

#     with pytest.raises(IndexError):
#         pq.pop()


# def test_int_to_ordinal():
#     assert int_to_ordinal(123) == '123rd'
#     assert int_to_ordinal(54) == '54th'
#     assert int_to_ordinal(57) == '57th'
#     assert int_to_ordinal(22) == '22nd'
#     assert int_to_ordinal(10101) == '10101st'


# def test_roman_to_int():
#     assert roman_to_int('IV') == 4
#     assert roman_to_int('VI') == 6
#     assert roman_to_int('IX') == 9
#     assert roman_to_int('LXX') == 70
#     assert roman_to_int('LXXX') == 80
#     assert roman_to_int('CM') == 900
#     assert roman_to_int('M') == 1000


# def test_int_to_roman():
#     assert int_to_roman(4) == 'IV'
#     assert int_to_roman(6) == 'VI'
#     assert int_to_roman(9) == 'IX'
#     assert int_to_roman(70) == 'LXX'
#     assert int_to_roman(80) == 'LXXX'
#     assert int_to_roman(900) == 'CM'
#     assert int_to_roman(1000) == 'M'


# def test_clamp():
#     assert clamp(0, 2, 5) == 2
#     assert clamp(100, 2, 5) == 5
#     assert clamp(50, 0, 100) == 50

#     with pytest.raises(ValueError):
#         assert clamp(10, 5, 0)
