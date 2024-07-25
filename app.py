from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from model import db, User, Section, Book, BookRequest, Rating
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

app = Flask(__name__)
app.secret_key = 'ab60a2e0a84f4a8798156574e3bd796b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

app.app_context().push()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password and not user.is_librarian:
                #auto revoke
                requests=BookRequest.query.filter_by(user_id=user.id).all()
                for req in requests:
                    # print(req.date_return<=datetime.now())
                    if req.status=='approved' and req.date_return<=datetime.now():
                        req.status='revoked'
                        db.session.commit()
                        flash('your Book has been revoked!', 'error')
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials', 'error')
                return redirect(url_for('login'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email=request.form['email']
        user= User.query.filter_by(username=username).first()
        if user:
            flash('User already exists', 'error')
            return redirect(url_for('register'))
        user = User(username=username, password=password,email=email,is_librarian=False)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/librarian_register', methods=['GET', 'POST'])
def librarian_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email=request.form['email']
        user= User.query.filter_by(username=username).first()
        if user:
            flash('User already exists', 'error')
            return redirect(url_for('librarian_register'))
        user = User(username=username, password=password,email=email,is_librarian=True)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('librarian_login'))
    return render_template('libregister.html')

@app.route('/librarian_login', methods=['GET', 'POST'])
def librarian_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password and user.is_librarian:
                login_user(user)
                return redirect(url_for('librarian_home'))
    return render_template('liblogin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')


@app.route('/librarian_home', methods=['GET', 'POST'])
@login_required
def librarian_home():
    sections=Section.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        query=request.form['query']
        sections=Section.query.filter(Section.name.like('%'+query+'%')).all()
        if sections:
            return render_template('librarian_home.html',sections=sections)
    return render_template('librarian_home.html',sections=sections)

@app.route('/add_section', methods=['GET', 'POST'])
@login_required
def add_section():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        date_created = request.form['date_created']
        date_created = datetime.strptime(date_created, '%Y-%m-%d')
        section= Section.query.filter_by(name=name).first()
        if section:
            flash('Section already exists', 'error')
            return redirect(url_for('add_section'))
        section = Section(name=name, description=description, user_id=current_user.id, date_created=date_created)
        db.session.add(section)
        db.session.commit()
        flash('Section added successfully', 'success')
        return redirect(url_for('librarian_home'))
    return render_template('add_section.html')

@app.route('/edit_section/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_section(id):
    section = Section.query.get(id)
    if request.method == 'POST':
        name=request.form['name']
        description=request.form['description']
        date_created = request.form['date_created']
        date_created = datetime.strptime(date_created, '%Y-%m-%d')
        section_exist= Section.query.filter_by(name=name,description=description,date_created=date_created).first()
        if section_exist:
            flash('Section already exists', 'error')
            return redirect(url_for('edit_section', id=id))
        section.name=name
        section.description=description
        section.date_created=date_created
        db.session.commit()
        flash('Section updated successfully', 'success')
        return redirect(url_for('librarian_home'))
    return render_template('edit_section.html', section=section)

@app.route('/delete_section/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_section(id):
    section = Section.query.get(id)
    for book in section.books:
        db.session.delete(book)
    db.session.delete(section)
    db.session.commit()
    flash('Section deleted successfully', 'success')
    return redirect(url_for('librarian_home'))

@app.route("/section_books/<int:id>", methods=['GET', 'POST'])
@login_required
def section_books(id):
    section=Section.query.filter_by(id=id).first()
    if request.method == 'POST':
        query=request.form['query']
        books=Book.query.filter(db.or_(Book.title.ilike(f"%{query}%"), Book.author.ilike(f"%{query}%"))).all()
        if books:
            return render_template('section_books.html',books=books,section=section)
    books=section.books
    return render_template('section_books.html',books=books,section=section)

@app.route('/add_book/<int:id>', methods=['GET', 'POST'])
@login_required
def add_book(id):
    section=Section.query.filter_by(id=id).first()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        date_return = request.form['date_return']
        date_return = datetime.strptime(date_return, '%Y-%m-%d')
        date_issued = request.form['date_issued']
        date_issued=datetime.strptime(date_issued, '%Y-%m-%d')
        book_exist= Book.query.filter_by(title=title).first()
        if book_exist:
            flash('Book already exists', 'error')
            return redirect(url_for('add_book', id=id))
        book = Book(title=title, author=author, content=content, section_id=id, date_return=date_return,date_issued=date_issued)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully', 'success')
        return redirect(url_for('section_books', id=id))
    return render_template('add_book.html',section=section)


@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get(id)
    if request.method == 'POST':
        title=request.form['title']
        author=request.form['author']
        content=request.form['content']
        date_return = request.form['date_return']
        date_return = datetime.strptime(date_return, '%Y-%m-%d')
        date_issued = request.form['date_issued']
        date_issued=datetime.strptime(date_issued, '%Y-%m-%d')
        book_exist= Book.query.filter_by(title=title,author=author,content=content,date_return=date_return,date_issued=date_issued).first()
        if book_exist:
            flash('Book already exists', 'error')
            return redirect(url_for('edit_book', id=id))
        book.title=title
        book.author=author
        book.content=content
        book.date_return=date_return
        book.date_issued=date_issued
        db.session.commit()
        flash('Book updated successfully', 'success')
        return redirect(url_for('section_books', id=book.section_id))
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_book(id):
    book = Book.query.get(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully', 'success')
    return redirect(url_for('section_books', id=book.section_id))

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    sections=Section.query.all()
    if request.method == 'POST':
        query=request.form['query']
        sections=Section.query.filter(Section.name.like('%'+query+'%')).all()
        if sections:
            return render_template('home.html',sections=sections)
        books = Book.query.filter(db.or_(Book.title.ilike(f"%{query}%"), Book.author.ilike(f"%{query}%"))).all()
        return render_template('booksearch.html', books=books)
    return render_template('home.html',sections=sections)


@app.route('/request/<int:id>', methods=['GET', 'POST'])
@login_required
def requests(id):
    book=Book.query.filter_by(id=id).first()
    if request.method == 'POST':
        book_request=BookRequest.query.filter_by(user_id=current_user.id,book_id=id).all()
        if book_request:
            book_request=BookRequest.query.filter_by(user_id=current_user.id,book_id=id).all()[-1]
            if book_request.status=='pending' or book_request.status=='approved':
                flash('Book already requested', 'error')
                return redirect(url_for('home'))
            if book_request.status=='revoked':
                flash('Book revoked by librarian, you can not access this book!', 'error')
                return redirect(url_for('home'))
        book_request=BookRequest.query.filter_by(user_id=current_user.id).all()
        count=0
        for req in book_request:
            if req.status=='approved':
                count+=1
        if count>=5:
            flash('You can not request more than 5 books at a time', 'error')
            return redirect(url_for('home'))
        date_return = request.form['date_return']
        date_return = datetime.strptime(date_return, '%Y-%m-%d')
        book_request=BookRequest(user_id=current_user.id,book_id=id,date_requested=datetime.now(),date_return=date_return,status='pending')
        db.session.add(book_request)
        db.session.commit()
        flash('Book requested successfully', 'success')
        return redirect(url_for('home'))
    return render_template('request.html',book=book)

@app.route('/mybooks', methods=['GET', 'POST'])
@login_required
def userrequests():
    def get_book_data(req):
        book = Book.query.filter_by(id=req.book_id).first()
        b_d = {}
        b_d['title'] = book.title
        b_d['author'] = book.author
        b_d['content'] = book.content
        b_d['date_return'] = req.date_return
        b_d['status'] = req.status
        b_d['rid'] = req.id
        b_d['bid'] = book.id
        b_d['is_rated'] = True if Rating.query.filter_by(user_id=current_user.id, book_id=req.book_id).first() else False
        return b_d

    requests = BookRequest.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        query = request.form['query']
        requests = BookRequest.query.filter(BookRequest.status.like('%' + query + '%')).all()
        if requests:
            books = [get_book_data(req) for req in requests]
            return render_template('mybooks.html', requests=books)
        books = Book.query.filter(db.or_(Book.title.ilike(f"%{query}%"), Book.author.ilike(f"%{query}%"))).all()
        if books:
            req=[]
            for i in books:
                requests = BookRequest.query.filter_by(user_id=current_user.id, book_id=i.id).all()
                for j in requests:
                    req.append(j)
            books = [get_book_data(req) for req in req]
            return render_template('mybooks.html', requests=books)
            

    books = [get_book_data(req) for req in requests]
    return render_template('mybooks.html', requests=books)

@app.route('/return/<int:id>', methods=['GET', 'POST'])
@login_required
def return_book(id):
    book_request=BookRequest.query.filter_by(id=id).first()
    book_request.status='returned'
    book_request.date_return=datetime.now()
    db.session.commit()
    flash('Book returned successfully', 'success')
    return redirect(url_for('userrequests'))

@app.route('/rate/<int:id>', methods=['GET', 'POST'])
@login_required
def rate_book(id):
    book=Book.query.filter_by(id=id).first()
    if request.method == 'POST':
        rating=Rating.query.filter_by(user_id=current_user.id,book_id=id).first()
        if rating:
            flash('Book already rated', 'error')
            return redirect(url_for('userrequests'))
        rating=Rating(user_id=current_user.id,book_id=id,rating=request.form['rating'],feedback=request.form['feedback'])
        db.session.add(rating)
        db.session.commit()
        flash('Book rated successfully', 'success')
        return redirect(url_for('userrequests'))
    return render_template('rate.html',book=book)

@app.route('/book_request', methods=['GET', 'POST'])
@login_required
def book_requests():
    user_id=current_user.id
    requests=BookRequest.query.join(Book).filter(Book.section_id==Section.id,Section.user_id==user_id).all()
    if request.method == 'POST':
        query=request.form['query']
        requests=BookRequest.query.join(Book).filter(Book.section_id==Section.id,Section.user_id==user_id,Book.title.like('%'+query+'%')).all()
        requests+=BookRequest.query.join(Book).filter(Book.section_id==Section.id,Section.user_id==user_id,Book.author.like('%'+query+'%')).all()
        requests+=BookRequest.query.filter(BookRequest.status.like('%'+query+'%')).all()
        if requests:
            return render_template('book_request.html',requests=requests)
    return render_template('book_request.html',requests=requests)

@app.route('/approve_request/<int:id>', methods=['GET', 'POST'])
@login_required
def approve_request(id):
    book_request=BookRequest.query.filter_by(id=id).first()
    book_request.status='approved'
    db.session.commit()
    flash('Request approved successfully', 'success')
    return redirect(url_for('book_requests'))

@app.route('/reject_request/<int:id>', methods=['GET', 'POST'])
@login_required
def reject_request(id):
    book_request=BookRequest.query.filter_by(id=id).first()
    db.session.delete(book_request)
    db.session.commit()
    flash('Request rejected successfully', 'success')
    return redirect(url_for('book_requests'))

@app.route('/revoke_book/<int:id>', methods=['GET', 'POST'])
@login_required
def revoke_book(id):
    book_request=BookRequest.query.filter_by(id=id).first()
    book_request.status='revoked'
    db.session.commit()
    flash('Book revoked successfully', 'success')
    return redirect(url_for('book_requests'))

@app.route('/book/<int:id>', methods=['GET', 'POST'])
@login_required
def book(id):
    book=Book.query.filter_by(id=id).first()
    return render_template('book.html',book=book)

@app.route('/librarian_book/<int:id>', methods=['GET', 'POST'])
@login_required
def librarian_book(id):
    book=Book.query.filter_by(id=id).first()
    return render_template('librarian_book.html',book=book)


@app.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
    book_requests=BookRequest.query.filter_by(status='returned',user_id=current_user.id).all()
    books={}
    for book_request in book_requests:
        book=Book.query.filter_by(id=book_request.book_id).first()
        if book.title not in books:
            books[book.title]=1
        else:
            books[book.title]+=1

    section={}
    for book_request in book_requests:
        book=Book.query.filter_by(id=book_request.book_id).first()
        if book.section.name not in section:
            section[book.section.name]=1
        else:
            section[book.section.name]+=1
    
    matplotlib.use('Agg')
    plt.clf()
    plt.figure(figsize=(10,5))
    sns.barplot(x=list(books.keys()),y=list(books.values()), palette='bright')
    plt.xlabel('Book Title')
    plt.ylabel('Number of Reads')
    plt.title('Book Read')
    plt.savefig('static/barplot.png')

    plt.clf()
    plt.figure(figsize=(10,5))
    plt.pie(x=list(section.values()), labels=list(section.keys()), autopct='%1.1f%%', startangle=90, colors=sns.color_palette('bright'))
    plt.title('Section Distribution')
    plt.savefig('static/pieplot.png')

    return render_template('stats.html')

@app.route('/librarian_stats')
def librarianstats():
    book_requests=BookRequest.query.filter((BookRequest.status=='approved') | (BookRequest.status=='returned') | (BookRequest.status=='revoked') ).all()
    books={}
    for book_request in book_requests:
        book=Book.query.filter_by(id=book_request.book_id).first()
        if book.title not in books:
            books[book.title]=1
        else:
            books[book.title]+=1

    section={}
    for book_request in book_requests:
        book=Book.query.filter_by(id=book_request.book_id).first()
        if book.section.name not in section:
            section[book.section.name]=1
        else:
            section[book.section.name]+=1
    
    matplotlib.use('Agg')
    plt.clf()
    plt.figure(figsize=(10,5))
    sns.barplot(x=list(books.keys()),y=list(books.values()), palette='bright')
    plt.xlabel('Book Title')
    plt.ylabel('Number of Issues')
    plt.title('Book Issued')
    plt.savefig('static/lbarplot.png')

    plt.clf()
    plt.figure(figsize=(10,5))
    plt.pie(x=list(section.values()), labels=list(section.keys()), autopct='%1.1f%%', startangle=90, colors=sns.color_palette('bright'))
    plt.title('Section Distribution')
    plt.savefig('static/lpieplot.png')

    return render_template('librarian_stats.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

