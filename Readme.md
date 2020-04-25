Welcome to the covid19 wiki! In lieu of the outbreak of COVID-19, the Purpose of this project is to enable people with limited resources (senior citizens, specially abled, economically weak, et. al) to reach out to people ready to volunteer. Every request will be tagged basis type of request: 
1. CRITICAL - for life-critical requirements
2. URGENT - for need of basic necessities (food/medicines)
3. OTHERS - for anything else

Check out the LIVE version here - www.covidsos.org


About the Files:
1. apis.py - This file contains the code for service created using Flask that runs all the APIs.
2. data_fetching.py - This file contains all functions that request "Reading" from the MySQL database.
3. database_entry.py - This file contains all functions that do "UPDATE" or "ADD/APPEND" options to MySQL database.
4. auth.py - This file contains login authentication related functions (both for Volunteer as well as Admin/moderator)
5. connections.py - This file contains functions that can be used to connect to different mySQL DBs (prod/staging) for both read and write purposes.
6. partner_assignment.py - This file contains code related to request assignment to a volunteer.
7. whatsapp_fn.py - WhatsApp related APIs/functions to be added here.
8. settings.py - contains values of constants/configurations
