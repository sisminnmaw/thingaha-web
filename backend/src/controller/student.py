"""API route for Student API"""
import traceback
from datetime import datetime

from flask import request, current_app, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from common.aws_client import get_s3_url
from common.config import S3_BUCKET
from common.error import SQLCustomError, RequestDataEmpty, ValidateFail, ThingahaCustomError
from controller.api import address_service
from controller.api import api, post_request_empty, custom_error, sub_admin, full_admin, get_default_address
from service.student.student_service import StudentService

student_service = StudentService()


@api.route("/students", methods=["GET"])
@jwt_required
@cross_origin()
def get_students():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        current_app.logger.info("Get all student records")
        return jsonify({
            "data": student_service.get_all_students(page, per_page)
        }), 200
    except SQLCustomError as error:
        current_app.logger.error("Error in get all student records")
        return jsonify({"errors": [error.__dict__]}), 400


@api.route("/students/<int:student_id>", methods=["GET"])
@jwt_required
@cross_origin()
def get_student_by_id(student_id: int):
    """
    get student by student id
    :return:
    """
    try:
        current_app.logger.info("Return data for student_id: {}".format(student_id))
        return jsonify({
            "data": {
                "student": student_service.get_student_by_id(student_id)
            }}), 200
    except SQLCustomError as error:
        current_app.logger.error("Return error for students: {}".format(student_id))
        return jsonify({"errors": [error.__dict__]}), 400


@api.route("/students", methods=["POST"])
@jwt_required
@sub_admin
@cross_origin()
def create_student():
    """
    create student by post body
    :return:
    """
    data = request.get_json()
    if data is None:
        return post_request_empty()
    try:
        address_data = data.get("address") if data.get("address") else get_default_address()
        address_id = address_service.create_address({
            "division": address_data.get("division"),
            "district": address_data.get("district"),
            "township": address_data.get("township"),
            "street_address": address_data.get("street_address"),
            "type": "student"
        }, flush=True)
        if not address_id:
            raise ThingahaCustomError("Student address create fail")

        student_id = student_service.create_student({
            "name": data.get("name"),
            "deactivated_at":  None if data.get("active") else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "birth_date": data.get("birth_date"),
            "father_name": data.get("father_name"),
            "mother_name": data.get("mother_name"),
            "parents_occupation": data.get("parents_occupation"),
            "photo": data.get("photo"),
            "address_id": address_id})
        current_app.logger.info("Create student success. student_name %s", data.get("name"))
        return get_student_by_id(student_id), 200
    except (RequestDataEmpty, SQLCustomError, ValidateFail, ThingahaCustomError) as error:
        current_app.logger.error("Create student request fail")
        return jsonify({"errors": [error.__dict__]}), 400


@api.route("/students/<int:student_id>", methods=["DELETE"])
@jwt_required
@full_admin
@cross_origin()
def delete_students(student_id: int):
    """
    delete student by ID
    :param student_id:
    :return:
    """
    try:
        current_app.logger.info("Delete student id: {}".format(student_id))
        student_delete_status = False
        student = student_service.get_student_by_id(student_id)
        if student_service.delete_student_by_id(student_id):
            if student.get("photo") and student_service.delete_file(student.get("photo")):
                current_app.logger.info("Student photo exists and delete the photo in s3")
            else:
                current_app.logger.warning("No photo or delete the photo in s3")
            student_delete_status = address_service.delete_address_by_id(student["address"]["id"])
        return jsonify({
            "status": student_delete_status
            }), 200
    except SQLCustomError as error:
        current_app.logger.error("Fail to delete student_id: %s".format(student_id))
        return jsonify({"errors": [error.__dict__]}), 400


@api.route("/students/<int:student_id>", methods=["PUT"])
@jwt_required
@sub_admin
@cross_origin()
def update_student(student_id: int):
    """
    update student by ID
    :param student_id:
    :return:
    """
    data = request.get_json()
    if data is None:
        return post_request_empty()

    student = student_service.get_student_by_id(student_id)
    if not student:
        return custom_error("Invalid student id supplied.")

    try:
        address_data = data.get("address")
        address_updated = True
        if address_data:
            address_updated = address_service.update_address_by_id(student["address"]["id"], {
                "division": address_data.get("division"),
                "district": address_data.get("district"),
                "township": address_data.get("township"),
                "street_address": address_data.get("street_address"),
                "type": "student"
            })

        if address_updated:
            student_update_status = student_service.update_student_by_id(student_id, {
                "name": data.get("name"),
                "deactivated_at": None if data.get("active") else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "birth_date": data.get("birth_date"),
                "father_name": data.get("father_name"),
                "mother_name": data.get("mother_name"),
                "parents_occupation": data.get("parents_occupation"),
                "photo": data.get("photo"),
                "address_id": student["address"]["id"]
            })
            if student_update_status:
                current_app.logger.info("Update success for student_id: {}".format(student_id))
                return get_student_by_id(student_id)
            else:
                current_app.logger.error("Update fail for student_id: {}".format(student_id))
                custom_error("Update Fail for student id: {}".format(student_id))

    except ValueError as error:
        current_app.logger.error("Value error for address id. error: %s", error)
        return jsonify({"errors": [error.__dict__]}), 400

    except (SQLCustomError, ValidateFail, RequestDataEmpty) as error:
        current_app.logger.error("Error for student data update id {} Error: {}"
                                 .format(student_id, error))
        return jsonify({"errors": [error.__dict__]}), 400


@api.route("/student/upload", methods=["POST"])
@jwt_required
@sub_admin
@cross_origin()
def upload_s3_file():
    """
    Upload a file to an S3 bucket
    :return: True if file was uploaded, else False
    """
    img = request.files.get("img")
    student_id = request.form.get("student_id")
    try:
        if student_id and int(student_id) not in StudentService.get_all_student_ids():
            raise ThingahaCustomError("Invalid student ID")
        if student_id is None or not img or img.filename == "":
            return post_request_empty()
        file_extension = student_service.allowed_file(img.filename)
        if not file_extension:
            return custom_error("File extension should be .png or .jpg or .jpeg")
        file_name = student_id + "." + file_extension
        result = student_service.upload_file(img, file_name)
        if result:
            url = get_s3_url().format(S3_BUCKET, file_name)
            if student_service.update_photo_path_by_id(student_id, url):
                return get_student_by_id(student_id), 200
        else:
            current_app.logger.error("Can't update student photo url for student id: {}".format(student_id))
            return "", 400
    except ThingahaCustomError as error:
        current_app.logger.error("Error for student photo upload {}".format(error.__dict__))
        return jsonify({"errors": [error.__dict__]}), 400
    except (ValueError, TypeError):
        current_app.logger.error("Value error for student photo upload error: {}".format(traceback.format_exc()))
        return jsonify({"errors": [ThingahaCustomError("Student ID must be integer").__dict__]}), 400


@api.route("/student/upload", methods=["PUT"])
@jwt_required
@sub_admin
@cross_origin()
def update_file():
    """
    update s3 file, delete file first and upload new files
    """
    old_url = request.form["old_url"]
    if not old_url:
        current_app.logger.error("Old url for student required")
        return post_request_empty()
    if not student_service.delete_file(old_url):
        current_app.logger.error("Can't delete file before update")
        return custom_error("Update file error")
    return upload_s3_file()


@api.route("/student/upload", methods=["DELETE"])
@jwt_required
@sub_admin
@cross_origin()
def delete_s3_file():
    """
    delete S3 file
    """
    data = request.get_json()
    url = data.get("url")
    student_id = data.get("student_id")
    if not url or not student_id:
        current_app.logger.error("Empty url or empty student id")
        return post_request_empty()

    try:
        if int(student_id) not in StudentService.get_all_student_ids():
            raise ThingahaCustomError("Invalid student ID")
        result = student_service.delete_file(url) and student_service.update_photo_path_by_id(student_id, "")
        if result:
            current_app.logger.info("Delete file for URL %s success", url)
            return "", 200
        else:
            current_app.logger.error("Delete file for URL %s fail", url)
            return "", 400
    except TypeError:
        current_app.logger.error("Student id must be integer")
        return custom_error("Student id must be integer")


@api.route("/students/search", methods=["GET"])
@jwt_required
@cross_origin()
def search_student():
    """
    search student with query
    search keyword in name, father_name, mother_name and parents_occupation
    """
    query = request.args.get("query")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("page", 20, type=int)
    try:
        current_app.logger.info("search student : query: %s", query)
        return jsonify({
            "data": student_service.get_students_by_query(page, query, per_page)
        }), 200
    except SQLCustomError as error:
        current_app.logger.error("Fail to search student : query: %s", query)
        return jsonify({"errors": [error.__dict__]}), 400
