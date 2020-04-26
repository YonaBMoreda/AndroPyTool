import csv
import play_scraper


def write_to_csv(filename, app_id):
    """
    Fetches and writes contextual data to csv file
    :param filename: the csv file destination
    :param app_id: the package id (Eg: 'com.whatsapp')
    :return:
    """
    app_details = play_scraper.details(app_id)
    # formatting the order of dictionary to have package id (pkgname) as the first column
    updated_dict = {"pkgname": app_details["app_id"]}
    del app_details["app_id"]
    updated_dict.update(app_details)
    file = open(filename, 'w+')
    with file:
        writer = csv.DictWriter(file, fieldnames=updated_dict.keys())
        writer.writeheader()
        writer.writerow(updated_dict)


write_to_csv('contextual_feat_whatsapp.csv', 'com.whatsapp')
