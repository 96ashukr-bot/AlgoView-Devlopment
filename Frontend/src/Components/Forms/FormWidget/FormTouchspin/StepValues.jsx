import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const StepValues = () => {
    const [val, setVal] = useState(20)
    const step = true
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Touchspin steps</H5><span>Add <code>.data-bts-step="VALUE"</code> attribute
                            for increament and decrement steps to touchspin input group.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} step={step} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default StepValues