import React, { Fragment } from "react";
import { useForm } from "react-hook-form";
import { Row, Col, Form, Label, FormGroup, Button } from "reactstrap";
import { FirstName, LastName, Next } from "../../../../Constant";

const Registration = ({ setSteps, setFormdata, formdata }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();
  const onSubmit = (data) => {
    setFormdata((prev) => ({ ...prev, ...data }));
    setSteps((prev) => prev + 1);
  };

  return (
    <Fragment>
      <Row>
        <Col sm="12">
          <Form onSubmit={handleSubmit(onSubmit)} className="form-bookmark needs-validation">
            <FormGroup className="mb-3">
              <Label htmlFor="fname">{FirstName}</Label>
              <input className={`form-control ${errors.firstName && "is-invalid"}`} id="fname" type="text" name="firstname" defaultValue={formdata.firstName || ""} {...register("firstName", { required: true })} />
              <span className="text-danger">{errors.firstName && "First name is required"}</span>
            </FormGroup>
            <FormGroup className="mb-3">
              <Label htmlFor="lname">{LastName}</Label>
              <input className={`form-control ${errors.lastname && "is-invalid"}`} id="lname" type="text" name="lastname" defaultValue={formdata.lastname || ""} {...register("lastname", { required: true })} />
              <span className="text-danger">{errors.lastname && "Last name is required"}</span>
            </FormGroup>
            <div className="text-end btn-mb">
              <Button className="primary">{Next}</Button>
            </div>
          </Form>
        </Col>
      </Row>
    </Fragment>
  );
};

export default Registration;
