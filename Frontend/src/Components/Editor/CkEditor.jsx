import { CKEditorExample } from '../../Constant';
import { Breadcrumbs, H1, H5, P } from '../../AbstractElements';
import React, { Fragment, useState } from 'react';
import CKEditors from 'react-ckeditor-component';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';

const CkEditorContain = () => {
    const [content, setContent] = useState('content');
    const onChange = (evt) => {
        const newContent = evt.editor.getData();
        setContent(newContent);
    };
    return (
        <Fragment>
            <Breadcrumbs mainTitle='CK Editor' parent="Editor" title="CK Editor" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <Card>
                            <CardHeader>
                                <H5>{CKEditorExample}</H5>
                            </CardHeader>
                            <CardBody>
                                <CKEditors
                                    activeclassName="p10"
                                    content={content}
                                    events={{
                                        'change': onChange
                                    }}
                                />
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
                <Row>
                    <Col sm="12">
                        <Card>
                            <CardHeader>
                                <H5>Inline Editor</H5>
                            </CardHeader>
                            <CardBody>
                                <div id="area1">
                                    {/* <ReactQuill /> */}
                                    <H1>Your title</H1>
                                    <P>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at vulputate urna, sed dignissim arcu. Aliquam at ligula imperdiet, faucibus ante a, interdum enim. Sed in mauris a lectus lobortis condimentum. Sed in nunc magna. Quisque massa urna, cursus vitae commodo eget, rhoncus nec erat. Sed sapien turpis, elementum sit amet elit vitae, elementum gravida eros. In ornare tempus nibh ut lobortis. Nam venenatis justo ex, vitae vulputate neque laoreet a.</P>
                                </div>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};
export default CkEditorContain;