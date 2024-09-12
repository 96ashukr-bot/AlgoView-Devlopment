import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Btn, H4, P, Image } from "../../../AbstractElements";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import logoWhite from "../../../assets/images/logo/Algotradelogo.png";
import "./KycUpdate.css";

const KycUpdate = ({ logoClassMain }) => {
  const [formValues, setFormValues] = useState({
    name: "",
    phoneNumber: "",
    dateOfBirth: "",
    idFront: null,
    idBack: null,
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [previewFront, setPreviewFront] = useState(null);
  const [previewBack, setPreviewBack] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues({
      ...formValues,
      [name]: value,
    });
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (type === "front") {
      setFormValues({
        ...formValues,
        idFront: file,
      });
      setPreviewFront(URL.createObjectURL(file));
    } else if (type === "back") {
      setFormValues({
        ...formValues,
        idBack: file,
      });
      setPreviewBack(URL.createObjectURL(file));
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

  const handleSubmit = (e) => {
    e.preventDefault();
    toast.success("KYC Updated Successfully!", {
      position: toast.POSITION.TOP_RIGHT,
      autoClose: 3000,
    });
    // Reset form values after successful submission
    setFormValues({
      name: "",
      phoneNumber: "",
      dateOfBirth: "",
      idFront: null,
      idBack: null,
    });
    setPreviewFront(null);
    setPreviewBack(null);
  };

  const nextStep = () => {
    if (currentStep === 1) setCurrentStep(2);
  };

  const previousStep = () => {
    if (currentStep === 2) setCurrentStep(1);
  };

  return (
    <section>
      <Container className="p-0 login-page" fluid={true}>
        <Row className="m-0">
          <Col className="p-0">
            <div className="login-card">
              <div>
                <div>
                  <Link
                    className={`logo ${logoClassMain ? logoClassMain : ""}`}
                    to={process.env.PUBLIC_URL}
                  >
                    <Image
                      attrImage={{
                        className: "img-fluids for-light",
                        src: logoWhite,
                        alt: "loginpage",
                      }}
                    />
                  </Link>
                </div>
                <div className="kyc-card">
                  <div className="">
                    <Form
                      className="theme-form login-form"
                      onSubmit={handleSubmit}
                    >
                      {currentStep === 1 && (
                        <div className="login-main">
                          {/* Personal Details Section */}
                          <h4>Personal Details</h4>
                          <p>Please fill in the details to update your KYC.</p>

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

                          <FormGroup>
                            <button
                              type="button"
                              className="btn btn-primary btn-clr d-block w-100"
                              onClick={nextStep}
                            >
                              Next
                            </button>
                          </FormGroup>
                          <P attrPara={{ className: "text-start" }}>
                            Already have a KYC ?
                            <a className="ms-2" href="/login">
                              Sign in
                            </a>
                          </P>
                        </div>
                      )}

                      {currentStep === 2 && (
                        <div className="login-main-new">
                          {/* Document Upload Section */}
                          <h4>Document Upload</h4>
                          <p>
                            Upload the necessary documents to verify your
                            identity.
                          </p>

                          <FormGroup>
                            <Label className="col-form-label m-0 pt-0">
                              Select Government ID Type{" "}
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

                          <Row>
                            <Col md={6}>
                              {/* Front ID Upload */}
                              <FormGroup>
                                <Label className="col-form-label m-0 pt-0">
                                  Upload ID Front{" "}
                                  <span className="text-danger">*</span>
                                </Label>
                                <div className="file-upload-wrapper">
                                  <Input
                                    className="form-control file-input"
                                    type="file"
                                    name="idFront"
                                    onChange={(e) =>
                                      handleFileChange(e, "front")
                                    }
                                    required
                                  />
                                  <p className="drag-text">
                                    Drag and drop file{" "}
                                  </p>
                                </div>
                              </FormGroup>
                            </Col>

                            <Col md={6}>
                              {/* Front ID Preview */}
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
                          </Row>

                          <Row>
                            <Col md={6}>
                              {/* Back ID Upload */}
                              <FormGroup>
                                <Label className="col-form-label m-0 pt-0">
                                  Upload ID Back{" "}
                                  <span className="text-danger">*</span>
                                </Label>
                                <div className="file-upload-wrapper">
                                  <Input
                                    className="form-control file-input"
                                    type="file"
                                    name="idBack"
                                    onChange={(e) =>
                                      handleFileChange(e, "back")
                                    }
                                    required
                                  />
                                  <p className="drag-text">
                                    Drag and drop file{" "}
                                  </p>
                                </div>
                              </FormGroup>
                            </Col>

                            <Col md={6}>
                              {/* Back ID Preview */}
                              {previewBack && (
                                <div className="image-preview">
                                  <img
                                    src={previewBack}
                                    alt="ID Back Preview"
                                  />
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

                          <FormGroup>
                            <button
                              type="button"
                              className="btn btn-primary d-block w-100 btn-pre-clr"
                              onClick={previousStep}
                            >
                              Previous
                            </button>
                          </FormGroup>

                          <FormGroup>
                            <Btn
                              attrBtn={{
                                className: "d-block w-100 btn-clr",
                                type: "submit",
                              }}
                            >
                              Update KYC
                            </Btn>
                          </FormGroup>
                          <P attrPara={{ className: "text-start" }}>
                            Already have a KYC ?
                            <a className="ms-2" href="/login">
                              Sign in
                            </a>
                          </P>
                        </div>
                      )}
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
