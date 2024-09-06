import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const HorizontalTouchspin = () => {
    const [val, setVal] = useState(70)
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Small Horizontal Touchspin</H5><span>Add <code>.input-group-sm</code>class to input-group.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default HorizontalTouchspin