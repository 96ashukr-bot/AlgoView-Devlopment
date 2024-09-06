import React, { Fragment, useState } from "react";
import { Card, CardBody, CardHeader, Col } from "reactstrap";
import { H5 } from "../../../../AbstractElements";
import Commen from "./Commen";

const MinMax = () => {
    const [val, setVal] = useState(22)
    return (
        <Fragment>
            <Col sm="12" md="6">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: "card-title" }}>Min Max Value of Touchspin</H5><span>Use <code>.data-bts-min="VALUE" data-bts-max="VALUE"</code>attribute to input to set min and max value
                            of touchspin input.</span>
                    </CardHeader>
                    <CardBody>
                        <Commen val={val} setVal={setVal} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}
export default MinMax