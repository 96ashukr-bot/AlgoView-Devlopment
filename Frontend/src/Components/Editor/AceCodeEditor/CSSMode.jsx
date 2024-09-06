import { H5 } from '../../../AbstractElements';
import { CssData } from './Data';
import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import AceEditor from 'react-ace';

const CssMode = () => {
    return (
        <Fragment>
            <Col xl="6">
                <Card>
                    <CardHeader>
                        <H5>CSS Mode</H5>
                    </CardHeader>
                    <CardBody>
                        <AceEditor
                            style={{ marginTop: '0px', width: '663px', height: '428px', marginLeft: '0px' }}
                            mode="css"
                            theme="monokai"
                            value={CssData}
                            name="blah2"
                            setOptions={{ useWorker: false }}
                            fontSize={14}
                            showPrintMargin={true}
                            showGutter={true}
                            editorProps={{ $blockScrolling: true }}
                            highlightActiveLine={true} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};
export default CssMode;