"""Initialize and seed local demonstration content."""
import argparse
import json
import os

from app import create_app
from models import (
    Category, CodingProblem, HRQuestion, MockTest, Question, TestQuestion,
    User, db,
)

CATEGORIES = [
    ("Java", "Core Java, collections, runtime, and language fundamentals."),
    ("Python", "Python language features, data types, and standard patterns."),
    ("C/C++", "C and C++ fundamentals, memory, and language behavior."),
    ("DBMS", "Relational data, transactions, normalization, and SQL."),
    ("Operating Systems", "Processes, memory, scheduling, and synchronization."),
    ("Computer Networks", "Networking layers, protocols, and common services."),
    ("Object-Oriented Programming", "Encapsulation, inheritance, abstraction, and polymorphism."),
    ("Data Structures and Algorithms", "Common data structures, complexity, and algorithms."),
    ("Aptitude", "Quantitative reasoning, logic, and basic problem solving."),
    ("HR Interview", "Behavioral interview concepts and professional communication."),
]

# Each tuple contains prompt, four options, correct option, explanation, difficulty.
QUESTION_BANK = {
    "Java": [
        ("Which Java collection preserves insertion order and permits duplicate elements?", ("HashSet", "ArrayList", "TreeSet", "EnumSet"), "B", "ArrayList maintains index order and permits duplicate values.", "Beginner"),
        ("What does the `final` keyword prevent when applied to a variable?", ("The variable being read", "The variable being assigned more than once", "The variable being passed to a method", "The variable being serialized"), "B", "A final variable can be assigned once and cannot then be reassigned.", "Beginner"),
        ("Which JVM memory area is shared by all threads?", ("Java stack", "Program counter", "Heap", "Native method stack"), "C", "Objects are allocated in the shared heap; each thread has its own stack.", "Beginner"),
        ("What is method overriding?", ("Defining two methods with different names", "A subclass providing an implementation of an inherited method", "Calling a method recursively", "Making a method static"), "B", "Overriding changes an inherited instance method implementation in a subtype.", "Intermediate"),
        ("Which type is appropriate for a value that may be absent and is not primitive?", ("Optional<T>", "volatile<T>", "synchronized<T>", "native<T>"), "A", "Optional<T> represents a present or absent reference value.", "Intermediate"),
        ("What does `synchronized` primarily provide for a method or block?", ("Compile-time type inference", "Mutual exclusion and memory visibility guarantees", "Object immutability", "Automatic persistence"), "B", "Synchronization coordinates access through a monitor and establishes visibility guarantees.", "Advanced"),
    ],
    "Python": [
        ("Which built-in type is immutable?", ("list", "dict", "set", "tuple"), "D", "A tuple cannot have its element references reassigned after creation.", "Beginner"),
        ("What does `enumerate(items)` provide while iterating?", ("Only item values", "Index-value pairs", "Sorted values", "A copy of the list"), "B", "enumerate yields pairs containing a count and each item.", "Beginner"),
        ("What is the purpose of a context manager used with `with`?", ("To repeat a block forever", "To manage setup and cleanup around a block", "To create a global variable", "To suppress every exception"), "B", "Context managers reliably perform cleanup when a block exits.", "Beginner"),
        ("What does a Python decorator commonly do?", ("Transforms or wraps a function or class", "Converts every value to a string", "Creates a new process", "Deletes a module"), "A", "Decorators take a callable and return a callable, often adding behavior.", "Intermediate"),
        ("What is the average lookup complexity of a dictionary by key?", ("O(1)", "O(log n)", "O(n)", "O(n log n)"), "A", "Hash-table lookup is average O(1), though worst cases can be slower.", "Intermediate"),
        ("Why should a mutable list generally not be used as a default argument?", ("Lists cannot be passed to functions", "The same default object is reused across calls", "It disables keyword arguments", "It forces recursion"), "B", "Default expressions are evaluated once when the function is defined.", "Advanced"),
    ],
    "C/C++": [
        ("Which operator obtains the address of an object in C?", ("*", "&", "->", "%"), "B", "The unary address-of operator is `&`.", "Beginner"),
        ("Which function safely reads a line with a size limit in standard C?", ("gets", "fgets", "scanf without a width", "puts"), "B", "fgets accepts a maximum buffer length and can read a line.", "Beginner"),
        ("What is the purpose of a C++ virtual destructor in a polymorphic base class?", ("Prevent all destruction", "Ensure derived destructors run when deleting through a base pointer", "Make the class abstract automatically", "Allocate objects on the stack"), "B", "A virtual destructor dispatches destruction through the dynamic type.", "Intermediate"),
        ("What does RAII associate a resource's lifetime with?", ("A global variable", "An object's lifetime", "The preprocessor", "A thread's priority"), "B", "RAII acquires resources during initialization and releases them on object destruction.", "Intermediate"),
        ("What is undefined behavior in C or C++?", ("A behavior guaranteed by the standard", "Behavior for which the standard imposes no requirements", "A compiler warning", "A runtime exception with a fixed message"), "B", "Undefined behavior permits the implementation to behave without standard constraints.", "Advanced"),
        ("Which smart pointer expresses exclusive ownership?", ("std::weak_ptr", "std::shared_ptr", "std::unique_ptr", "std::optional"), "C", "unique_ptr provides single-owner semantics and is movable.", "Intermediate"),
    ],
    "DBMS": [
        ("What is a primary key?", ("A column that may contain duplicate NULL values", "A column or column set uniquely identifying each row", "An index that stores only text", "A foreign table"), "B", "A primary key uniquely identifies each row and cannot be NULL.", "Beginner"),
        ("What does a foreign key enforce?", ("Referential integrity between related tables", "A unique value in every column", "Automatic encryption", "A fixed row order"), "A", "Foreign keys constrain references to valid rows in another or the same table.", "Beginner"),
        ("Which ACID property means a transaction is all-or-nothing?", ("Consistency", "Isolation", "Durability", "Atomicity"), "D", "Atomicity ensures a transaction fully succeeds or is rolled back.", "Beginner"),
        ("What is the main goal of normalization?", ("Increase duplicate data", "Reduce redundancy and update anomalies", "Remove all indexes", "Avoid using keys"), "B", "Normalization organizes relations to limit redundancy and anomalies.", "Intermediate"),
        ("What does an index generally trade for faster lookups?", ("Additional storage and write overhead", "Loss of all constraints", "Removal of the table", "Automatic backups"), "A", "Indexes consume storage and require maintenance on writes.", "Intermediate"),
        ("Under repeatable read, what problem is typically prevented compared with read committed?", ("Dirty reads", "Non-repeatable reads", "All deadlocks", "All phantom rows in every DBMS"), "B", "Repeatable read keeps previously read rows stable within the transaction; phantom handling varies by database.", "Advanced"),
    ],
    "Operating Systems": [
        ("What is a process?", ("A program currently being executed with its state", "A source file only", "A CPU instruction", "A network packet"), "A", "A process is an executing program together with resources and execution state.", "Beginner"),
        ("Which scheduler selects a ready process for CPU execution?", ("Long-term scheduler", "CPU/short-term scheduler", "I/O scheduler only", "Memory allocator"), "B", "The short-term scheduler chooses among ready processes for the CPU.", "Beginner"),
        ("What is a context switch?", ("Changing a source-code branch", "Saving one execution state and restoring another", "Restarting the operating system", "Clearing all memory"), "B", "The OS saves a running task's state and loads another's state.", "Beginner"),
        ("Which condition is necessary for deadlock?", ("Mutual exclusion", "Compilation", "Cache coherence", "Paging"), "A", "Mutual exclusion is one of the four Coffman conditions for deadlock.", "Intermediate"),
        ("What is virtual memory used for?", ("To let processes use an address space mapped to physical memory", "To eliminate storage devices", "To run without RAM", "To make every instruction atomic"), "A", "Virtual memory provides address translation and supports isolation and paging.", "Intermediate"),
        ("Why can a semaphore be useful?", ("To coordinate access to shared resources", "To encrypt a disk", "To compile code", "To replace every process"), "A", "Semaphores provide synchronization and resource-counting primitives.", "Advanced"),
    ],
    "Computer Networks": [
        ("Which protocol resolves a domain name to an IP address?", ("DNS", "DHCP", "SMTP", "SSH"), "A", "DNS maps domain names to records including IP addresses.", "Beginner"),
        ("Which transport protocol provides ordered, reliable byte-stream delivery?", ("UDP", "TCP", "ICMP", "ARP"), "B", "TCP provides reliable, ordered stream delivery with retransmission.", "Beginner"),
        ("What is the purpose of an IP router?", ("Forward packets between networks", "Render web pages", "Store passwords", "Assign source code types"), "A", "Routers forward packets according to network-layer routing information.", "Beginner"),
        ("Which HTTP method is conventionally safe and idempotent for retrieving a resource?", ("POST", "PATCH", "GET", "CONNECT"), "C", "GET is defined as a safe retrieval method and is idempotent by convention and semantics.", "Intermediate"),
        ("What does TLS primarily provide for an authenticated connection?", ("Confidentiality and integrity in transit", "Guaranteed application uptime", "Database normalization", "Faster DNS only"), "A", "TLS protects transport data and authenticates a peer when certificate validation succeeds.", "Intermediate"),
        ("What is the role of a subnet mask or prefix length?", ("Identify network and host portions of an IP address", "Encrypt the packet payload", "Choose a TCP port", "Authenticate a user"), "A", "The prefix indicates which IP bits identify the network.", "Advanced"),
    ],
    "Object-Oriented Programming": [
        ("Which principle bundles state and behavior behind a controlled interface?", ("Encapsulation", "Compilation", "Normalization", "Scheduling"), "A", "Encapsulation groups data and operations while controlling access.", "Beginner"),
        ("What is abstraction in object-oriented design?", ("Exposing relevant behavior while hiding implementation details", "Copying every field", "Making all methods public", "Storing objects in a database"), "A", "Abstraction focuses on essential behavior and omits unnecessary implementation detail.", "Beginner"),
        ("What is polymorphism?", ("One interface supporting different implementations", "A class with no methods", "A variable that never changes", "A database relationship"), "A", "Polymorphism allows callers to use a shared contract with varying implementations.", "Beginner"),
        ("Which relationship best represents a `Car` having an `Engine` as a required part?", ("Composition", "Unrelated dependency", "Compilation", "Overloading"), "A", "Composition models ownership of a component whose lifecycle is tied to its whole.", "Intermediate"),
        ("Why prefer composition over inheritance in many designs?", ("It always uses less memory", "It can reduce coupling to a base-class hierarchy", "It eliminates interfaces", "It prevents testing"), "B", "Composition can combine behavior without inheriting fragile implementation details.", "Intermediate"),
        ("What does the Liskov Substitution Principle require?", ("Subtypes should remain usable wherever their base type is expected", "Every class must have one method", "All fields must be public", "Subtypes must add new state"), "A", "Subtypes should preserve the behavioral expectations of the base abstraction.", "Advanced"),
    ],
    "Data Structures and Algorithms": [
        ("Which data structure follows last-in, first-out ordering?", ("Queue", "Stack", "Heap", "Graph"), "B", "A stack removes the most recently added item first.", "Beginner"),
        ("What is the time complexity of binary search on a sorted array?", ("O(1)", "O(log n)", "O(n)", "O(n²)"), "B", "Each comparison halves the remaining search interval.", "Beginner"),
        ("Which data structure is commonly used for breadth-first search?", ("Stack", "Queue", "Hash only", "Disjoint set only"), "B", "BFS processes vertices in discovery order using a queue.", "Beginner"),
        ("What property defines a min-heap?", ("Every parent is no greater than its children", "Every level is sorted left to right", "All values are unique", "The root is the maximum"), "A", "A min-heap maintains the heap-order property with the smallest element at the root.", "Intermediate"),
        ("What is the average lookup time in a well-distributed hash table?", ("O(1)", "O(log n)", "O(n)", "O(n log n)"), "A", "Hash tables provide average constant-time lookup under a suitable hash distribution.", "Intermediate"),
        ("Which algorithmic technique solves a problem by combining solutions to subproblems?", ("Divide and conquer", "Linear probing", "Breadth-first serialization", "Reference counting"), "A", "Divide and conquer splits a problem, solves subproblems, and combines results.", "Advanced"),
    ],
    "Aptitude": [
        ("A task takes 6 hours at a constant rate. What fraction is completed in 2 hours?", ("1/2", "1/3", "2/3", "1/6"), "B", "At a constant rate, 2 of 6 hours completes one third of the task.", "Beginner"),
        ("A product costing 80 is sold for 100. What is the profit percentage on cost?", ("20%", "25%", "30%", "80%"), "B", "Profit is 20; 20 divided by the cost 80 is 25%.", "Beginner"),
        ("The average of 6, 8, and 10 is:", ("6", "7", "8", "9"), "C", "Their sum is 24, and 24 divided by 3 is 8.", "Beginner"),
        ("If 5 workers complete a job in 12 days at equal rates, how many worker-days are required?", ("17", "30", "60", "72"), "C", "The total work is 5 × 12 = 60 worker-days.", "Intermediate"),
        ("A number increases from 40 to 50. What is the percentage increase?", ("10%", "20%", "25%", "50%"), "C", "The increase is 10; 10 divided by the starting value 40 is 25%.", "Intermediate"),
        ("A train travels 150 km in 2.5 hours. Its average speed is:", ("50 km/h", "60 km/h", "75 km/h", "90 km/h"), "B", "Average speed equals distance divided by time: 150/2.5 = 60 km/h.", "Beginner"),
    ],
    "HR Interview": [
        ("Which response is most useful when asked about a professional weakness?", ("Claim to have no weaknesses", "Describe a genuine growth area and concrete improvement steps", "Blame a former teammate", "Avoid answering"), "B", "A specific, honest example with improvement actions demonstrates self-awareness.", "Beginner"),
        ("What is a strong way to answer “Tell me about yourself”?", ("Recite unrelated personal details", "Give a concise role-focused summary of skills, evidence, and goals", "Read your entire resume", "Discuss confidential information"), "B", "A concise professional summary connects experience and motivation to the role.", "Beginner"),
        ("In the STAR method, what does the “A” represent?", ("Audience", "Action", "Achievement only", "Assessment"), "B", "STAR stands for Situation, Task, Action, and Result.", "Beginner"),
        ("How should you respond when you do not know an interview answer?", ("Invent facts confidently", "Explain what you know and how you would investigate", "End the interview", "Criticize the question"), "B", "Transparent reasoning and a learning approach are more credible than fabrication.", "Intermediate"),
        ("What is a constructive way to discuss a team disagreement?", ("Focus on personal blame", "Describe listening, evidence, collaboration, and outcome", "Share private details", "Say disagreement never happens"), "B", "A balanced example shows communication and problem-solving.", "Intermediate"),
        ("Before an interview, which action is most useful?", ("Research the role and prepare relevant examples", "Memorize a fabricated story", "Ignore the job description", "Avoid preparing questions"), "A", "Role research helps tailor accurate examples and thoughtful questions.", "Beginner"),
    ],
}

CODING_DATA = [
    {
        "title": "Find the largest element",
        "description": "Given a non-empty integer array, return its greatest value. Do not sort the array just to find the answer.",
        "constraints": "1 <= len(nums) <= 100,000; -1,000,000 <= nums[i] <= 1,000,000.",
        "hint": "Keep the largest value seen so far and compare each next element with it.",
        "explanation": "Initialize the running maximum with the first array value. Scan the rest once, replacing the maximum whenever a larger number appears. This works for all-negative arrays too because it does not assume zero is in the input. Time: O(n); extra space: O(1).",
        "cases": [("[3, 9, 2]", "9"), ("[-8, -3, -11]", "-3"), ("[5]", "5")],
    },
    {
        "title": "Reverse a string",
        "description": "Given a string, return a new string with its characters in reverse order. An empty string should remain empty.",
        "constraints": "0 <= len(s) <= 100,000; input contains ordinary Unicode text.",
        "hint": "Think about reading characters from the final index back to the first.",
        "explanation": "The character at index i moves to index len(s)-1-i. A reverse traversal or the language's slicing operation creates the result without changing the original string. Time: O(n); output space: O(n).",
        "cases": [('"interview"', "weivretni"), ('"a"', "a"), ('""', "")],
    },
    {
        "title": "Check prime number",
        "description": "Given an integer n, return True if n is prime and False otherwise. A prime is greater than 1 and has no positive divisors except 1 and itself.",
        "constraints": "0 <= n <= 10^9.",
        "hint": "After handling values below 2, it is enough to test candidate divisors up to the square root of n.",
        "explanation": "Values below 2 are not prime. For larger values, if n has a factor greater than sqrt(n), its paired factor must be smaller than sqrt(n), so testing beyond the square root is unnecessary. Stop as soon as a divisor is found. Time: O(sqrt(n)); extra space: O(1).",
        "cases": [("17", "True"), ("1", "False"), ("49", "False"), ("2", "True")],
    },
    {
        "title": "Palindrome string",
        "description": "Given a string s, return True when it reads identically from left to right and right to left; otherwise return False. Compare characters exactly.",
        "constraints": "0 <= len(s) <= 100,000; comparison is case-sensitive and includes spaces.",
        "hint": "Compare matching characters from the two ends and move inward.",
        "explanation": "A string is a palindrome if every character at index i matches the character at the mirrored index len(s)-1-i. You only need to inspect half the string. Under the stated exact comparison, capitalization and spaces are significant. Time: O(n); extra space: O(1) with two pointers.",
        "cases": [('"level"', "True"), ('"python"', "False"), ('""', "True"), ('"Aa"', "False")],
    },
    {
        "title": "Factorial",
        "description": "Return n factorial (n!), the product of every positive integer from 1 through n. By definition, 0! equals 1.",
        "constraints": "0 <= n <= 20; return an integer.",
        "hint": "Start with a product of 1, then multiply by each integer from 2 through n.",
        "explanation": "Repeatedly multiply an accumulator by 2, 3, ..., n. For n=5 the intermediate products are 1, 2, 6, 24, 120. The loop naturally returns 1 for n=0. Time: O(n); extra space: O(1).",
        "cases": [("5", "120"), ("0", "1"), ("1", "1"), ("3", "6")],
    },
    {
        "title": "Fibonacci sequence",
        "description": "Return a list containing the first n Fibonacci numbers, starting with 0 and 1. Each later number is the sum of the two before it.",
        "constraints": "0 <= n <= 40.",
        "hint": "Keep the previous two values, append the current one, then advance the pair.",
        "explanation": "Begin with an empty result and a pair (0, 1). Repeat n times: append the first value, then replace the pair with (second, first + second). This also handles n=0 without a special output. Time: O(n); output space: O(n).",
        "cases": [("7", "[0, 1, 1, 2, 3, 5, 8]"), ("0", "[]"), ("1", "[0]"), ("2", "[0, 1]")],
    },
    {
        "title": "Sum array elements",
        "description": "Given an integer array, return the sum of all its values. The empty array has sum 0.",
        "constraints": "0 <= len(nums) <= 100,000; -10,000 <= nums[i] <= 10,000.",
        "hint": "Start a running total at zero and add each element once.",
        "explanation": "Initialize total to 0 and add every array value. Negative numbers reduce the total; duplicates are added each time they appear. With no values, total remains 0. Time: O(n); extra space: O(1).",
        "cases": [("[4, -1, 2]", "5"), ("[]", "0"), ("[-2, -3]", "-5"), ("[7]", "7")],
    },
    {
        "title": "Count vowels",
        "description": "Count the English vowels a, e, i, o, and u in a string, treating uppercase and lowercase as the same. The letter y is not a vowel for this problem.",
        "constraints": "0 <= len(s) <= 100,000; s contains English letters and spaces.",
        "hint": "Normalize each character's case and check whether it belongs to the set {a, e, i, o, u}.",
        "explanation": "Walk through the characters and increment a counter when the lowercase character is one of a, e, i, o, or u. Each character is checked once. Time: O(n); extra space: O(1).",
        "cases": [('"Smart"', "1"), ('"Interview"', "4"), ('"rhythm"', "0"), ('""', "0")],
    },
    {
        "title": "Sort an array",
        "description": "Given an integer array, return its values in non-decreasing order. Keep duplicates; the input array may be empty.",
        "constraints": "0 <= len(nums) <= 100,000; -10^9 <= nums[i] <= 10^9.",
        "hint": "Use a comparison-based sort, or implement merge sort if practicing the algorithm.",
        "explanation": "A standard library sort returns the values in ascending order and keeps equal values. For algorithm practice, merge sort divides the array, sorts each half, and merges the sorted halves. Time: O(n log n) for an efficient comparison sort; output space depends on the chosen algorithm.",
        "cases": [("[4, 1, 3]", "[1, 3, 4]"), ("[5, 1, 5, -2]", "[-2, 1, 5, 5]"), ("[]", "[]")],
    },
    {
        "title": "Find duplicate values",
        "description": "Return each value that occurs more than once, exactly once, ordered by the position where its second occurrence appears.",
        "constraints": "0 <= len(nums) <= 100,000; nums contains integers.",
        "hint": "Track values already seen and values already added to the output.",
        "explanation": "Scan left to right. When a value has appeared before and is not yet in the duplicate list, append it. This defines the output order by the first time a duplicate is detected. A set makes membership checks average O(1). Time: O(n) average; extra space: O(n).",
        "cases": [("[1, 2, 1, 3, 2]", "[1, 2]"), ("[4, 4, 4]", "[4]"), ("[1, 2, 3]", "[]"), ("[]", "[]")],
    },
    {
        "title": "Armstrong number",
        "description": "Return True if a non-negative integer equals the sum of each of its digits raised to the number of digits. Treat 0 as an Armstrong number.",
        "constraints": "0 <= n <= 10^9.",
        "hint": "Convert the number to digits, count the digits, and sum each digit raised to that count.",
        "explanation": "For 153 there are three digits, and 1^3 + 5^3 + 3^3 = 153, so it is an Armstrong number. For 10, 1^2 + 0^2 = 1, which is not 10. A single digit n satisfies n^1=n. Time: O(d), where d is the number of digits.",
        "cases": [("153", "True"), ("10", "False"), ("0", "True"), ("9474", "True")],
    },
    {
        "title": "Second-largest distinct value",
        "description": "Return the second-largest distinct value in an integer array. Return None if the array contains fewer than two distinct values.",
        "constraints": "0 <= len(nums) <= 100,000; nums contains integers.",
        "hint": "Track the largest and second-largest distinct values; do not treat a duplicate maximum as the runner-up.",
        "explanation": "Scan once while maintaining the top two distinct values. When a new value exceeds the largest, move the old largest into second place. Otherwise update second only when the value is below largest and above the current second. Time: O(n); extra space: O(1).",
        "cases": [("[8, 3, 8, 5]", "5"), ("[7, 7]", "None"), ("[-5, -2, -9]", "-5"), ("[]", "None")],
    },
    {
        "title": "Character frequencies",
        "description": "Return a mapping from each character in a string to its number of occurrences. Treat uppercase and lowercase as different characters.",
        "constraints": "0 <= len(s) <= 100,000; input may contain letters, digits, or spaces.",
        "hint": "Use a dictionary and increment the count for each character as you scan.",
        "explanation": "For each character, increase its dictionary count by one, starting from zero when first seen. The result contains one key per distinct character. For example, in 'aba', a appears twice and b appears once. Time: O(n) average; extra space: O(k), where k is the number of distinct characters.",
        "cases": [('"aba"', "{'a': 2, 'b': 1}"), ('""', "{}"), ('"Aa "', "{'A': 1, 'a': 1, ' ': 1}")],
    },
    {
        "title": "Remove duplicates",
        "description": "Return the array with duplicates removed while preserving the order of each value's first appearance.",
        "constraints": "0 <= len(nums) <= 100,000; nums contains integers.",
        "hint": "Use a set to test whether a value has appeared, but append to a list to preserve order.",
        "explanation": "Scan from left to right. If a number is not in the seen set, append it to the result and add it to seen. Later copies are skipped. The set is only used for lookup; the result list preserves original first-seen order. Time: O(n) average; extra space: O(n).",
        "cases": [("[3, 1, 3, 2]", "[3, 1, 2]"), ("[5, 5, 5]", "[5]"), ("[]", "[]")],
    },
    {
        "title": "Missing number",
        "description": "An array contains n distinct values chosen from the range 0 through n, with exactly one value missing. Return the missing value.",
        "constraints": "0 <= len(nums) <= 100,000; every value is unique and 0 <= nums[i] <= len(nums).",
        "hint": "The sum of 0 through n is n(n+1)/2. Subtract the actual array sum.",
        "explanation": "Compute the expected sum for all n+1 values, then subtract the sum of the n values in the array. The difference is the missing number. This method uses constant extra space and does not need to sort. Time: O(n); extra space: O(1).",
        "cases": [("[3, 0, 1]", "2"), ("[0, 1]", "2"), ("[1]", "0"), ("[]", "0")],
    },
]

HR_DATA = [
    ("Tell me about yourself.", "A concise role-focused summary of your background, strengths, and next goal.", "Keep it relevant to the position and under two minutes.", "Introduction"),
    ("What are your strengths?", "Choose a strength and support it with a specific example and outcome.", "Use evidence rather than a list of adjectives.", "Self-awareness"),
    ("What is one area you are improving?", "Name a genuine growth area and describe the steps you are taking.", "Avoid disguising a strength as a weakness.", "Self-awareness"),
    ("Why should we hire you?", "Connect role requirements to your relevant skills and evidence.", "Use two or three concise points tied to the job description.", "Motivation"),
    ("Why do you want to join our company?", "Explain a researched connection between the role, company work, and your goals.", "Be specific and authentic; avoid generic praise.", "Motivation"),
    ("Where do you see yourself in five years?", "Describe realistic growth and contribution aligned with the role.", "Show ambition while staying open to learning.", "Career goals"),
    ("Describe a challenge you overcame.", "Use Situation, Task, Action, Result to explain your contribution.", "Emphasize your decisions and what you learned.", "Behavioral"),
    ("Tell me about a time you worked in a team.", "Share a team goal, your contribution, and the outcome.", "Recognize collaborators while clarifying your own role.", "Teamwork"),
    ("How do you handle pressure?", "Explain a practical method for prioritization and communication.", "Support the method with a real example.", "Behavioral"),
    ("What are your career goals?", "Discuss skills you want to build and impact you hope to make.", "Connect near-term goals to the role.", "Career goals"),
    ("Tell me about a mistake you made.", "Describe accountability, correction, and a lesson applied later.", "Do not shift blame or disclose sensitive information.", "Behavioral"),
    ("How do you prioritize competing deadlines?", "Explain how you assess impact, urgency, dependencies, and communicate trade-offs.", "Give an example if possible.", "Work habits"),
    ("What motivates you?", "Describe the kind of work and outcomes that genuinely engage you.", "Connect your answer to responsibilities in the role.", "Motivation"),
    ("How do you respond to feedback?", "Explain how you clarify, act on, and follow up on feedback.", "Give a concrete example of improvement.", "Work habits"),
    ("Describe a time you showed leadership.", "Explain how you helped a group make progress, regardless of title.", "Focus on actions and shared outcomes.", "Behavioral"),
    ("How would your classmates or colleagues describe you?", "Use a few evidence-backed traits consistent with how others work with you.", "Avoid unsupported superlatives.", "Self-awareness"),
    ("What do you know about this role?", "Summarize key responsibilities and the skills you bring to them.", "Review the job description before the interview.", "Motivation"),
    ("What do you do when you disagree with a teammate?", "Describe respectful listening, evidence, and a solution-focused discussion.", "Show how you preserve the working relationship.", "Teamwork"),
    ("What accomplishment are you proud of?", "Choose a relevant achievement and explain the effort and impact.", "Be precise about your personal contribution.", "Behavioral"),
    ("Do you have questions for us?", "Ask about success measures, team collaboration, or learning opportunities.", "Prepare thoughtful role-specific questions.", "Closing"),
]


def seed_data(admin_email=None, admin_password=None, demo=False):
    categories = {}
    for name, description in CATEGORIES:
        category = Category.query.filter_by(name=name).first()
        if not category:
            category = Category(name=name, description=description)
            db.session.add(category)
        categories[name] = category
    db.session.flush()

    for name, entries in QUESTION_BANK.items():
        for text, options, correct, explanation, difficulty in entries:
            if not Question.query.filter_by(question_text=text).first():
                db.session.add(Question(
                    category_id=categories[name].id, question_text=text,
                    question_type="mcq", difficulty=difficulty,
                    option_a=options[0], option_b=options[1],
                    option_c=options[2], option_d=options[3],
                    correct_answer=correct, explanation=explanation,
                    tags=name.lower(),
                ))
    for problem_data in CODING_DATA:
        cases = [
            {"input": sample_input, "output": sample_output}
            for sample_input, sample_output in problem_data["cases"]
        ]
        problem = CodingProblem.query.filter_by(title=problem_data["title"]).first()
        if not problem:
            problem = CodingProblem(title=problem_data["title"], difficulty="Beginner")
            db.session.add(problem)
        problem.description = problem_data["description"]
        problem.input_format = "Input is shown as a Python value in each example. Implement a function that accepts this value."
        problem.output_format = "Return the result in the same representation as the expected output."
        problem.sample_input = cases[0]["input"]
        problem.sample_output = cases[0]["output"]
        problem.constraints = problem_data["constraints"]
        problem.hints = problem_data["hint"]
        problem.solution_explanation = problem_data["explanation"]
        problem.test_cases_json = json.dumps(cases)
    for question, example, tips, category in HR_DATA:
        if not HRQuestion.query.filter_by(question_text=question).first():
            db.session.add(HRQuestion(
                question_text=question, example_answer=example,
                answer_tips=tips, category=category,
            ))
    db.session.flush()

    for category_name in ("Java", "Python", "DBMS", "Operating Systems", "Aptitude"):
        category = categories[category_name]
        if not MockTest.query.filter_by(title=f"{category_name} Quick Check").first():
            test = MockTest(
                title=f"{category_name} Quick Check",
                description=f"A short multiple-choice assessment for {category_name}.",
                category_id=category.id, duration_minutes=15, passing_percentage=50,
            )
            db.session.add(test)
            db.session.flush()
            questions = Question.query.filter_by(category_id=category.id, question_type="mcq").limit(6).all()
            for question in questions:
                db.session.add(TestQuestion(test_id=test.id, question_id=question.id, marks=1))

    email = admin_email or os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = admin_password or os.environ.get("ADMIN_PASSWORD", "")
    if demo:
        email = email or "admin@example.com"
        password = password or "DemoAdmin2026!"
        print("DEVELOPMENT DEMO ONLY: admin@example.com / DemoAdmin2026!")
    if email and password:
        admin = User.query.filter_by(email=email).first()
        if not admin:
            admin = User(full_name="Platform Admin", email=email, role="admin")
        admin.role = "admin"
        admin.is_active = True
        admin.set_password(password)
        db.session.add(admin)
    elif not User.query.filter_by(role="admin").first():
        raise ValueError("Set ADMIN_EMAIL and ADMIN_PASSWORD, or run seed.py --demo for local development.")
    db.session.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop and recreate the configured database")
    parser.add_argument("--demo", action="store_true", help="use a documented development-only demo admin")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        if args.reset:
            db.drop_all()
            db.create_all()
        seed_data(demo=args.demo)
        print(
            f"Seed complete: {Category.query.count()} categories, "
            f"{Question.query.count()} questions, {MockTest.query.count()} tests, "
            f"{CodingProblem.query.count()} coding problems, {HRQuestion.query.count()} HR questions."
        )


if __name__ == "__main__":
    main()
