import React, { Fragment } from "react";
import { Row, Col, Form, Label, Button, FormGroup } from "reactstrap";
import { Submit, BirthDate, Age, Previous } from "../../../../Constant";
import { useForm } from "react-hook-form";

const Birthdate = ({ setSteps, setFormdata, formdata }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();
  const onSubmit = (data) => {
    if (data) {
      setFormdata((prev) => ({ ...prev, ...data }));
      alert("Your Form is Submited");
      setSteps(1);
    }
  };
  return (
    <Fragment>
      <Row>
        <Col sm="12">
          <Form onSubmit={handleSubmit(onSubmit)} className="form-bookmark needs-validation">
            <FormGroup className="mb-3">
              <Label htmlFor="Bdate">{BirthDate}</Label>
              <input className={`form-control ${errors.birthday && "is-invalid"}`} id="Bdate" type="date" name="birthday" defaultValue={formdata.birthday || ""} {...register("birthday", { required: true })} />
              <span className="text-danger">{errors.birthday && "Birth Date is required"}</span>
            </FormGroup>
            <FormGroup className="mb-3">
              <Label htmlFor="age">{Age}</Label>
              <input className={`form-control ${errors.age && "is-invalid"}`} id="age" type="number" name="age" defaultValue={formdata.age || ""} {...register("age", { required: true })} />
              <span className="text-danger">{errors.age && "Age is required"}</span>
            </FormGroup>
            <div className="text-end">
              <Button className="secondary me-2" onClick={() => setSteps((pre) => pre - 1)}>
                {Previous}
              </Button>
              <Button className="primary" type="submit">
                {Submit}
              </Button>
            </div>
          </Form>
        </Col>
      </Row>
    </Fragment>
  );
};

export default Birthdate;
