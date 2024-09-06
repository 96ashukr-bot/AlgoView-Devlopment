import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const LargeHorizontal = () => {
    const [val, setVal] = useState(10)
    const large = true
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Large Horizontal Touchspin</H5><span>Add <code>.input-group-lg</code>class to input-group.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} large={large} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default LargeHorizontal