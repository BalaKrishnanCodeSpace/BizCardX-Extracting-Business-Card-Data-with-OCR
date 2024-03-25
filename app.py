import streamlit as st                              # Used for creating the web application
from streamlit_option_menu import option_menu       # Used for creating a custom option menu
import mysql.connector                              # Used for interacting with MySQL database
import pandas as pd                                 # Used for data manipulation
import easyocr                                      # Used for optical character recognition
import cv2                                          # Used for image processing
import os                                           # Used for file operations
import matplotlib.pyplot as plt                     # Used for plotting
import re                                           # Used for regular expressions
import numpy as np                                  # Used for numerical operations
from PIL import Image                               # Used for image processing
import time                                         # Used for timing operations

def create_database_and_table():
    """
    Establishes a connection to the MySQL database server, creates a database named 'BizcardX' if it doesn't exist,
    and creates a table named 'Card_Details' if it doesn't exist within the 'BizcardX' database.

    Returns:
        tuple: A tuple containing the MySQL connection object and cursor object.
    """
    # Establish connection to MySQL database server
    mySqlConnection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
    )
    
    # Create a cursor object to execute SQL queries
    myCursor = mySqlConnection.cursor()

    # Retrieve a list of existing databases on the MySQL server
    myCursor.execute("SHOW DATABASES")
    databases = [database[0] for database in myCursor.fetchall()]
    
    # Create 'BizcardX' database if it doesn't exist
    if "bizcardx" not in databases:
        myCursor.execute("CREATE DATABASE BizcardX")
        mySqlConnection.commit()
    
    # Close cursor and database connection to open a new connection to the 'BizcardX' database
    myCursor.close()
    mySqlConnection.close()
    mySqlConnection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="BizcardX"
    )    
    myCursor = mySqlConnection.cursor()
    
    # Create 'Card_Details' table if it doesn't exist within the 'BizcardX' database
    myCursor.execute('''CREATE TABLE IF NOT EXISTS Card_Details
                        (
                            Card_Holder TEXT,
                            Company_Name TEXT,
                            Designation TEXT,
                            Mobile_Number VARCHAR(50),
                            E_Mail_Id TEXT,
                            Website TEXT,
                            Area TEXT,
                            City TEXT,
                            State TEXT,
                            Pin_Code VARCHAR(10),
                            Image LONGBLOB
                        )'''
    )

    # Commit changes to the database
    mySqlConnection.commit()

    return mySqlConnection, myCursor


    
def set_page(page):
    """
    Sets the current page of the Streamlit application.

    Args:
        page (str): The name of the page to be set as the current page.

    Returns:
        None
    """
    st.session_state.current_page = page



@st.cache_data
def loadImage():
    """
    Loads the OCR (Optical Character Recognition) reader for processing images.

    Returns:
        easyocr.Reader: An OCR reader object configured for English language.
    """
    reader = easyocr.Reader(['en'], model_storage_directory=".")
    return reader


def save_card(uploaded_card):
    """
    Saves the uploaded business card image to a designated directory.

    Args:
        uploaded_card: Uploaded business card image.

    Returns:
        None
    """
    if not os.path.exists("uploaded_cards"):
        # Check if a directory named "uploaded_cards" exists in the current directory,
        # if not, create one.
        os.makedirs("uploaded_cards")

    with open(os.path.join("uploaded_cards", uploaded_card.name), "wb") as f:
        # Write the contents of the uploaded card buffer to a file in the "uploaded_cards" directory.
        f.write(uploaded_card.getbuffer())

        
def imagePreview(image,res): 
    """
    Display bounding boxes and extracted text on the given image.

    Args:
        image: Image to display.
        res: List of tuples containing bounding box coordinates, extracted text, and probability.

    Returns:
        None
    """
    for (boundingBox, text, prob) in res: 
        # Unpack the bounding box coordinates
        (tl, tr, br, bl) = boundingBox  # tl - top-left, tr - top-right, br - bottom-right, bl - bottom-left
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        print(tl,tr,br,bl, sep = " ")
        
        # Draw rectangle around the detected text
        cv2.rectangle(image, tl, br, (0, 255, 0), 2)
        # Add text label to the detected text
        cv2.putText(image, text, (tl[0], tl[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    # Configure plot settings and display the image
    plt.rcParams['figure.figsize'] = (15,15)
    plt.axis('off')
    plt.imshow(image)


def fetchData(card):
    """
    Extract relevant information from the text extracted from a business card.

    Args:
        card (str): Text extracted from the business card.

    Returns:
        dict: A dictionary containing the extracted information including:
            - ContactNumber: Extracted contact number(s).
            - Pincode: Extracted pin code.
            - E_Mail_id: Extracted email address.
            - Website: Extracted website URL.
            - Card_Holder_Name: Extracted card holder's name.
            - Designation: Extracted designation.
            - Company_Name: Extracted company name.
            - City: Extracted city.
            - State: Extracted state.
            - Address: Extracted address.
    """
    # Define patterns for replacing, matching, and extracting information from the card text
    
    replacing=[
        (';',""),
        (',',''),
        ('.com','com'),
        ('com','.com'),
        ('WWW ','www.'),
        ("www ", "www."),
        ('www', 'www.'),
        ('www.','www'),
        ('wWW','www'),
        ('wwW','www')
    ]

    # Replace specific patterns in the card text
    for old, new in replacing:
        card = card.replace(old, new)

    # Extract Contact Number(s)
    contactPattern = r"\+*\d{2,3}-\d{3,4}-\d{4}"
    match1 = re.findall(contactPattern, card)
    ContactNumber = '; '.join(match1)
    card = re.sub(contactPattern, '', card)
        
    # Extract Pincode
    pincodePattern=r"\d+"
    Pincode = ''
    match2=re.findall(pincodePattern,card)
    for code in match2:
        if len(code)==6 or len(code)==7:
            Pincode=Pincode+code
            card=card.replace(code,"")
    
    # Extract Email Address    
    emailIdPattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}\b"
    E_Mail_id = ''
    match3=re.findall(emailIdPattern,card)
    for ids in match3:
        E_Mail_id = E_Mail_id + ids.lower()
        card=card.replace(ids,'')

    # Extract Website URL
    webUrlPattern=r"www\.[A-Za-z0-9]+\.[A-Za-z]{2,3}"
    Website = ''
    match4=re.findall(webUrlPattern,card)
    for url in match4:
        Website = url.lower() + Website
        card=card.replace(url,"")

    # Extract alpha words from the result
    alpha_patterns = r'^[A-Za-z]+ [A-Za-z]+$|^[A-Za-z]+$|^[A-Za-z]+ & [A-Za-z]+$'
    alpha_var=[]
    for i in result:
        if re.findall(alpha_patterns,i):
            if i not in 'WWW':
                alpha_var.append(i)
                card=card.replace(i,"")
    
    # Extract Card Holder's Name
    Card_Holder_Name = alpha_var[0].title()
    
    # Extract Designation Company Name
    Designation=alpha_var[1].title()
    
    # Extract Company Name
    if len(alpha_var)==3:
        Company_Name=alpha_var[2].title()
    else:
        Company_Name=alpha_var[2].title()+" "+alpha_var[3].title()
    
    # Extract City, State and Address    
    new_card=card.split()
    if new_card[4]=='St':
            City=new_card[2]
    else:
            City=new_card[3]
    if new_card[4]=="St":
            State=new_card[3]
    else:
            State=new_card[4]
    if new_card[4]=='St':
            Address=new_card[0]+" "+new_card[4]+" "+new_card[1]
    else:
            Address=new_card[0]+" "+new_card[1]+" "+new_card[2]
    
    # Return a dictionary containing the extracted information
    return {
        "ContactNumber": ContactNumber,
        "Pincode": Pincode,
        "E_Mail_id": E_Mail_id,
        "Website": Website,
        "Card_Holder_Name": Card_Holder_Name,
        "Designation": Designation,
        "Company_Name": Company_Name,
        "City": City,
        "State": State,
        "Address": Address
    }


# -- * -- * -- * -- * -- * -- * -- * -- Streamlit -- * -- * -- * -- * -- * -- * -- * -- #

logo_image = "https://github.com/BalaKrishnanCodeSpace/Bizcard/blob/72cb279bf708aae7ed276664e8b82df8273d36ae/Heading.png?raw=true"

# Setting the page configuration
st.set_page_config(page_title= "BizCardX - Extracting Business Card Data",
                   page_icon= logo_image,
                   layout= "wide",
                   initial_sidebar_state= "expanded"
                   )

# Hiding default formatting for the main menu and footer
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

# Background image URL
backgroundImageUrl = "https://static.vecteezy.com/system/resources/previews/026/307/268/non_2x/cool-plain-blue-abstract-background-hd-wallpaper-design-free-vector.jpg"

# Add a custom CSS style to set the background image
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url('{backgroundImageUrl}');
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Defining layout columns
col1, col2, col3 = st.columns([3, 2, 8])

# Displaying logo in the first column
with col1:
    logo_image = "https://github.com/BalaKrishnanCodeSpace/Bizcard/blob/72cb279bf708aae7ed276664e8b82df8273d36ae/Heading.png?raw=true"
    st.image(logo_image, use_column_width=False, width=300)

# Empty space in the second column
with col2:
    st.write("")

# Generating the option menu with icons
with col3:
    st.write("")
    st.write("")
    st.write("")
    selected = option_menu(
        menu_title = None,
        options=["Home","Extract","Modify"],
        default_index= 0,
        icons =["house-fill","collection-fill","table"],
        orientation="horizontal",
        styles={
        "container": {"background-color": "#D1EDF9", "height": "46px", "width" : "880px","size":"cover", "display" : "flex", "justify-content": "center"},
        "icon": {"color": "#2569B0", "font-size": "19px"},
        "nav-link": { "--hover-color": "#5B9BD5","color": "#2860AB","width":"150px",
                        "text-align":"center","padding":"3px 5",
                        "border-bottom":"6px solid transparent","transition":"border-bottom 0.3 ease","font-size":"14px"},
        "nav-link:hover": {"color":"yellow"},
        "nav-link-selected": {"background-color": "white", "width":"150px","border-bottom":"3px solid #2569B0","color":"#2860AB"}
        }           
    )
    
# Adding a horizontal rule to enhance visual appeal
st.markdown('<hr style="height:2px;border:none;background-color:#5B9BD5;width:36.2cm;margin:0;padding:0;" />', unsafe_allow_html=True)

# Displaying the welcome message and information about BizCardX when the "Home" option is selected
if selected == "Home":
    # Adding empty lines for spacing
    st.write("")
    st.write("")
    st.write("")
    
    # Displaying the header with a markdown title
    st.markdown("# Welcome to BizCardX - Business Card Data Extraction")
    st.write("")
    st.write("")
    
    # Displaying information about BizCardX with markdown
    st.markdown(" ### About BizCardX")
    st.markdown(
                """
                ####
                BizCardX is a powerful tool designed to help you effortlessly extract essential information from business cards. 
                Whether you're networking at events, receiving business cards from clients, or simply organizing your contacts, 
                BizCardX makes it easy to digitize and manage business card data."""
    )
    st.write("")
    st.write("")
    
    # Displaying key features with markdown
    st.markdown("""
                ### Key Features

                - **Image Upload:** Simply upload an image of a business card, and BizCardX will extract relevant information automatically.

                - **EasyOCR Integration:** Powered by easyOCR, BizCardX ensures accurate extraction of company names, cardholder names, contact details, and more.

                - **Database Management:** Save extracted information along with business card images to a database for easy access and organization.

                - **CRUD Operations:** Perform Create, Read, Update, and Delete operations on stored business card entries directly from the application interface.

                - **Simple and Intuitive:** With a clean and intuitive user interface, BizCardX makes managing business card data a breeze.
                """
    )

# Processing the selected option "Extract"
if selected == "Extract":
    st.write("")
    st.write("")
    st.markdown("#### Upload your card to extract the detail")
    col1,col2 =st.columns([5,10])
    with col1:
        uploadCard = st.file_uploader("Upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])
    if uploadCard is not None:
        # Reading the uploaded image file
        file_bytes = uploadCard.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        uploadedCard = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Displaying the uploaded image and processing the uploaded image for text extraction
        coll, colr = st.columns(2, gap = "large")
        with coll:
            st.markdown("#     ")
            st.write()
            st.markdown("### Uploaded Card")
            st.write()
            st.image(uploadedCard, channels='BGR', width=652, caption="Uploaded image")
            # Saving the uploaded card to the local directory
            save_card(uploadCard)
        with colr:
            st.markdown("#     ")
            st.write()
            # Processing the uploaded image to extract text
            with st.spinner("Please wait while the image is being processed"):
                reader = loadImage()
                result = reader.readtext(np.array(uploadedCard), detail=0)
                imageWithText = uploadedCard.copy()
                card = " ".join(result)
                # Extracting information from the processed text
                cardInfo = fetchData(card)
                st.markdown("### Processed Image and Extracted Information")
                st.write()
                st.set_option('deprecation.showPyplotGlobalUse', False)
                savedImage = os.getcwd()+"\\"+"uploaded_cards" + "\\" + uploadCard.name
                image = cv2.imread(savedImage)
                imgResult = reader.readtext(savedImage)    
                # Displaying the processed image with extracted text
                st.pyplot(imagePreview(image,imgResult))
                # Retrieving extracted information
                Card_Holder_Name = cardInfo.get("Card_Holder_Name", "")
                Company_Name = cardInfo.get("Company_Name", "")
                Designation = cardInfo.get("Designation", "")
                Contact_Number = cardInfo.get("ContactNumber", "")
                E_Mail_Id = cardInfo.get("E_Mail_id", "")
                Web_Url = cardInfo.get("Website", "")
                Address = cardInfo.get("Address", "")
                City = cardInfo.get("City", "")
                State = cardInfo.get("State", "")
                Pincode = cardInfo.get("Pincode", "")
        st.write("")
        st.write("")
        st.write("")
        # Displaying extracted data in tabs
        tab1, tab2, tab3 = st.tabs([":blue[**Extracted Data⠀⠀⠀⠀**]", ":blue[**Cleaned Data⠀⠀⠀⠀**]", ":blue[**Upload to MySql⠀⠀⠀⠀**]"])
        with tab1:
            st.write("")
            st.write(result)
        with tab2:
            # Displaying cleaned extracted data in columns
            col1,col2,col3 = st.columns([1.3,2.1,8])
            with col1:
                st.write("")
                st.write(f'<div style="color: red;">⠀Name</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Company Name</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Designation</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Contact Number</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Email Id</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Website URL</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Address</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀City</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀Pincode</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="color: red;">⠀State</div>', unsafe_allow_html=True)         
            with col2:    
                st.write("")            
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Card_Holder_Name}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Company_Name}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Designation}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Contact_Number}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{E_Mail_Id}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Web_Url}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Address}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{City}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{Pincode}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write(f'<div style="background-color: #F1F8FF; color: #2772B6;">⠀{State}</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
            with col3:
                pass
        with tab3:
            st.write("")
            st.write("Click below button to upload the cleaned data into database along with uploaded image")
            st.write("")
            st.write("")
            submit = st.button("Upload to Database")
            if submit:
                mySqlConnection, myCursor = create_database_and_table()
                myCursor.execute("SELECT COUNT(*) FROM card_details WHERE E_Mail_Id = %s", (E_Mail_Id,))
                result = myCursor.fetchone()
                email_exists = result[0] > 0
                if email_exists:
                    # If email ID exists, update the record 
                    sql = """UPDATE card_details 
                            SET Card_Holder = %s, Company_Name = %s, Designation = %s, Mobile_Number = %s, 
                                Website = %s, Area = %s, City = %s, State = %s, Pin_Code = %s, Image = %s 
                            WHERE E_Mail_Id = %s"""
                    data = (Card_Holder_Name, Company_Name, Designation, Contact_Number, Web_Url, Address, City, State, Pincode, file_bytes, E_Mail_Id)
                    myCursor.execute(sql, data)
                else:
                    # If email ID doesn't exist, insert a new record
                    sql = """INSERT INTO card_details 
                            (Card_Holder, Company_Name, Designation, Mobile_Number, E_Mail_Id, Website, 
                            Area, City, State, Pin_Code, Image) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    data = (Card_Holder_Name, Company_Name, Designation, Contact_Number, E_Mail_Id, Web_Url, Address, City, State, Pincode, file_bytes)
                    myCursor.execute(sql, data)
                mySqlConnection.commit()
                st.write("")
                st.write("")
                col1,col2 = st.columns([10,15])
                with col1:
                    st.success("#### Uploaded to database successfully!")
                with col2:
                    st.write()
                myCursor.close()
                mySqlConnection.close()

# Processing the selected option "Modify"
if selected == "Modify":
    # Creating database connection and cursor
    mySqlConnection, myCursor = create_database_and_table()
    # Retrieving all records from the card_details table
    myCursor.execute("SELECT * FROM card_details")
    result = myCursor.fetchall()
    # Converting the result into a pandas DataFrame
    df = pd.DataFrame(result, columns = myCursor.column_names)
    df.index = df.index+1
    df.index.name = 'S No'
    # Retrieving unique company names
    companyNames = df["Company_Name"].unique()
    cola, colb = st.columns([2.38,5])
    with cola:
        st.write("")
        st.write("")
        st.markdown("<b style='color: #2569B0; font-size: 16px;'>Please select your desired option</b>", unsafe_allow_html=True)
    with colb:
        subSelection = st.radio("", ("View Data⠀⠀⠀⠀⠀⠀⠀", "Update or Delete"))
        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;} </style>', unsafe_allow_html=True)
    if subSelection == "View Data⠀⠀⠀⠀⠀⠀⠀":
        st.markdown("#     ")
        st.write(df)
    if subSelection == "Update or Delete":
        colx,coly,colz = st.columns([1.9,2,2])
        with colx:
            st.write("")
            st.write("")
            st.markdown("<b style='color: #2569B0; font-size: 16px;'>Select the desired Company Name to Update/Delete the detail</b>", unsafe_allow_html=True)
        with coly:
            selectedCompany = st.selectbox("", companyNames)
        with colz:
            st.write()
        st.markdown("#     ")
        st.markdown('<hr style="height:0.2px;border:none;background-color:#5B9BD5;width:14.1cm;margin:0;padding:0;" />', unsafe_allow_html=True)
        if selectedCompany:
            companyDetails = df[df["Company_Name"] == selectedCompany].iloc[0]
            colx,coly,colz = st.columns([0.44,1.5,3])
            with colx:
                st.markdown("#     ")
                st.write("###### Card Holder")
                st.markdown("#     ")
                st.write("")
                st.write("###### Designation")
                st.markdown("#     ")
                st.write("")
                st.write("###### Mobile Number")
                st.markdown("##     ")
                st.write("")
                st.write("###### Email ID")
                st.markdown("##     ")
                st.write("")
                st.write("###### Website")
                st.markdown("##     ")
                st.write("")
                st.write("###### Area")
                st.markdown("##     ")
                st.write("")
                st.write("###### City")
                st.markdown("##     ")
                st.write("")
                st.write("###### State")
                st.markdown("##     ")
                st.write("")
                st.write("###### Pin Code")
            with coly:
                companyDetails["Card_Holder"] = st.text_input("Card Holder", companyDetails["Card_Holder"],label_visibility="hidden")
                companyDetails["Designation"] = st.text_input("Designation", companyDetails["Designation"],label_visibility="hidden")
                companyDetails["Mobile_Number"] = st.text_input("Mobile Number", companyDetails["Mobile_Number"],label_visibility="hidden")
                companyDetails["E_Mail_Id"] = st.text_input("Email ID", companyDetails["E_Mail_Id"],label_visibility="hidden")
                companyDetails["Website"] = st.text_input("Website", companyDetails["Website"],label_visibility="hidden")
                companyDetails["Area"] = st.text_input("Address", companyDetails["Area"],label_visibility="hidden")
                companyDetails["City"] = st.text_input("City", companyDetails["City"],label_visibility="hidden")
                companyDetails["State"] = st.text_input("State", companyDetails["State"],label_visibility="hidden")
                companyDetails["Pin_Code"] = st.text_input("Pin Code", companyDetails["Pin_Code"],label_visibility="hidden")
            with colz:
                st.write("")
            st.markdown("#    ")
            st.markdown("#    ")
            col1, col2 = st.columns([0.5,4])
            if col1.button("Update"):
                sql = """UPDATE card_details 
                        SET Card_Holder = %s, Designation = %s, Mobile_Number = %s, E_Mail_Id = %s,
                            Website = %s, Area = %s, City = %s, State = %s, Pin_Code = %s
                        WHERE Company_Name = %s"""
                val = (
                    companyDetails["Card_Holder"], companyDetails["Designation"], companyDetails["Mobile_Number"],
                    companyDetails["E_Mail_Id"], companyDetails["Website"], companyDetails["Area"],
                    companyDetails["City"], companyDetails["State"], companyDetails["Pin_Code"], selectedCompany
                )
                myCursor.execute(sql, val)
                mySqlConnection.commit()
                st.success(f"Modified details updated successfully!")
                time.sleep(3)
                st.experimental_rerun()
            if col2.button("Delete"):
                sql = "DELETE FROM card_details WHERE Company_Name = %s"
                val = (selectedCompany,)
                myCursor.execute(sql, val)
                mySqlConnection.commit()
                st.success(f"Record for {selectedCompany} deleted successfully!")
                time.sleep(3)
                st.experimental_rerun()
    mySqlConnection.close()
    myCursor.close()