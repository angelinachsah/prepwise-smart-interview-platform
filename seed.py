"""Initialize and seed local demonstration content."""
import argparse
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
    ("Find the largest element", "Return the greatest integer in a non-empty array.", "[3, 9, 2]", "9", "Input is a non-empty list of integers.", "Compare values while scanning once."),
    ("Reverse a string", "Return the characters of a string in reverse order.", "interview", "weivretni", "Input is a string.", "Build from the final character toward the first."),
    ("Check prime number", "Determine whether an integer greater than one is prime.", "17", "True", "Input is an integer.", "Test divisors only up to the square root."),
    ("Palindrome string", "Check whether a string reads the same forward and backward.", "level", "True", "Compare exact characters.", "Compare the string with its reverse."),
    ("Factorial", "Compute n! for a non-negative integer n.", "5", "120", "0 <= n <= 20.", "Start with one and multiply through n."),
    ("Fibonacci sequence", "Return the first n Fibonacci numbers beginning with 0, 1.", "7", "[0, 1, 1, 2, 3, 5, 8]", "0 <= n <= 40.", "Keep the previous two values."),
    ("Sum array elements", "Return the sum of all integers in an array.", "[4, -1, 2]", "5", "Array may be empty.", "Accumulate each value."),
    ("Count vowels", "Count English vowels in a string, ignoring case.", "Smart", "1", "Input contains ordinary English characters.", "Normalize case and test membership in a vowel set."),
    ("Sort an array", "Return integers in ascending order.", "[4, 1, 3]", "[1, 3, 4]", "Input may include duplicates.", "Use a comparison-based sort or explain its complexity."),
    ("Find duplicate values", "Return distinct values that appear more than once.", "[1, 2, 1, 3, 2]", "[1, 2]", "Return duplicates in first repeated-value order.", "Track values seen and values already reported."),
    ("Armstrong number", "Check whether a non-negative integer equals the sum of its digits raised to the digit count.", "153", "True", "Input is non-negative.", "For 153: 1³ + 5³ + 3³ equals 153."),
    ("Second-largest distinct value", "Return the second-largest distinct integer, or None if absent.", "[8, 3, 8, 5]", "5", "Input can contain duplicates.", "Track the largest two distinct values."),
    ("Character frequencies", "Count each character in a string.", "aba", "{'a': 2, 'b': 1}", "Treat characters as case-sensitive.", "Use a dictionary keyed by character."),
    ("Remove duplicates", "Return the values of an array in first-seen order without duplicates.", "[3, 1, 3, 2]", "[3, 1, 2]", "Input contains hashable integers.", "Use a seen set and preserve traversal order."),
    ("Missing number", "Given unique values from 0 through n with one missing, return the missing value.", "[3, 0, 1]", "2", "Input length is n and values are in [0,n].", "Compare the expected arithmetic sum with the actual sum."),
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
    for title, description, sample_input, sample_output, constraints, hints in CODING_DATA:
        if not CodingProblem.query.filter_by(title=title).first():
            db.session.add(CodingProblem(
                title=title, description=description, difficulty="Beginner",
                input_format="One value in the displayed sample format.",
                output_format="Return the expected result in the displayed format.",
                sample_input=sample_input, sample_output=sample_output,
                constraints=constraints, hints=hints,
                solution_explanation=hints,
            ))
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
