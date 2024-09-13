import React, { useState } from "react";
// import { Link } from "react-router-dom";
// import { P } from "../../../../AbstractElements";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./KycUpdate.css";
import { updateKYC } from "../../../../Services/Authentication";

const KycUpdate = ({}) => {
  const [formValues, setFormValues] = useState({
    name: "",
    phoneNumber: "",
    dateOfBirth: "",
    idFront: null,
    idBack: null,
    idType: "",
  });
  const [previewFront, setPreviewFront] = useState(null);
  const [previewBack, setPreviewBack] = useState(null);
  const [isFormValid, setIsFormValid] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues((prevValues) => {
      const updatedValues = { ...prevValues, [name]: value };

      const allFilled =
        updatedValues.name &&
        updatedValues.phoneNumber &&
        updatedValues.dateOfBirth &&
        updatedValues.idType;

      setIsFormValid(allFilled);

      return updatedValues;
    });
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];

    if (file) {
      if (type === "front") {
        setFormValues({ ...formValues, idFront: file });
        setPreviewFront(URL.createObjectURL(file));
      } else if (type === "back") {
        setFormValues({ ...formValues, idBack: file });
        setPreviewBack(URL.createObjectURL(file));
      }
    }
  };

  const handleRemoveImage = (type) => {
    if (type === "front") {
      setFormValues({ ...formValues, idFront: null });
      setPreviewFront(null);
    } else if (type === "back") {
      setFormValues({ ...formValues, idBack: null });
      setPreviewBack(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (
      !formValues.name ||
      !formValues.phoneNumber ||
      !formValues.dateOfBirth ||
      !formValues.idType
    ) {
      toast.error("All fields are required", {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });
      return;
    }

    try {
      const response = await updateKYC(formValues);
      toast.success("KYC Updated Successfully!", {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });

      setFormValues({
        name: "",
        phoneNumber: "",
        dateOfBirth: "",
        idFront: null,
        idBack: null,
        idType: "",
      });
      setPreviewFront(null);
      setPreviewBack(null);
      setIsFormValid(false);
    } catch (error) {
      toast.error(error.message, {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });
    }
  };

  return (
    <section>
      <Container className="p-0 login-page" fluid={true}>
        <Row className="m-0">
          <Col className="p-0">
            <div className="login-card">
              <div>
                <div className="kyc-card">
                  <div className="">
                    <Form
                      className="theme-form login-form"
                      onSubmit={handleSubmit}
                      encType="multipart/form-data"
                    >
                      <div className="login-main-new">
                        <div className="kyc-main-head">
                          <h2>Update Your KYC</h2>
                        </div>
                        {/* Personal Details Section */}
                        <h4>Personal Details</h4>
                        <p>Please fill in the details to update your KYC.</p>

                        <Row>
                          <Col md={4}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0">
                                Name <span className="text-danger">*</span>
                              </Label>
                              <Input
                                className="form-control"
                                type="text"
                                name="name"
                                value={formValues.name}
                                onChange={handleInputChange}
                                required
                                placeholder="Enter Your Name"
                              />
                            </FormGroup>
                          </Col>

                          <Col md={4}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0">
                                Phone Number{" "}
                                <span className="text-danger">*</span>
                              </Label>
                              <Input
                                className="form-control"
                                type="tel"
                                name="phoneNumber"
                                value={formValues.phoneNumber}
                                onChange={handleInputChange}
                                required
                                placeholder="Enter Your Phone Number"
                              />
                            </FormGroup>
                          </Col>

                          <Col md={4}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0">
                                Date of Birth{" "}
                                <span className="text-danger">*</span>
                              </Label>
                              <Input
                                className="form-control"
                                type="date"
                                name="dateOfBirth"
                                value={formValues.dateOfBirth}
                                onChange={handleInputChange}
                                required
                              />
                            </FormGroup>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            {/* ID Type Dropdown */}
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 gov-id-head">
                                Select Government ID{" "}
                                <span className="text-danger">*</span>
                              </Label>
                              <Input
                                type="select"
                                name="idType"
                                className="form-control"
                                value={formValues.idType}
                                onChange={handleInputChange}
                                required
                              >
                                <option value="" disabled>
                                  Select ID Type
                                </option>
                                <option value="Aadhar Card">Aadhar Card</option>
                                <option value="PAN Card">PAN Card</option>
                                <option value="Passport">Passport</option>
                                <option value="Voter Id">Voter Id</option>
                                <option value="Driving License">
                                  Driving License
                                </option>
                              </Input>
                            </FormGroup>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            {/* Front ID Upload */}
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Front{" "}
                                <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="idFront"
                                  onChange={(e) => handleFileChange(e, "front")}
                                  required
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewFront && (
                              <div className="image-preview">
                                <img
                                  src={previewFront}
                                  alt="ID Front Preview"
                                />
                                <button
                                  className="remove-image"
                                  onClick={() => handleRemoveImage("front")}
                                >
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>

                          <Col md={6}>
                            {/* Back ID Upload */}
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Back{" "}
                                <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="idBack"
                                  onChange={(e) => handleFileChange(e, "back")}
                                  required
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewBack && (
                              <div className="image-preview">
                                <img src={previewBack} alt="ID Back Preview" />
                                <button
                                  className="remove-image"
                                  onClick={() => handleRemoveImage("back")}
                                >
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>
                        </Row>

                        <div className="text-center">
                          <button
                            type="submit"
                            className="btn btn-primary btn-clr update-btn"
                            disabled={!isFormValid}
                          >
                            Update
                          </button>
                        </div>
                      </div>
                    </Form>
                  </div>
                </div>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
      <ToastContainer />
    </section>
  );
};

export default KycUpdate;
