import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const DecimalValues = () => {
    const [val, setVal] = useState(53.25)
    const decimal = true
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Decimal Value of Touchspin</H5><span>Use <code>data-bts-decimal="VALUE"</code>  attribute to use decimal value of touchspin input.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} decimal={decimal} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default DecimalValues