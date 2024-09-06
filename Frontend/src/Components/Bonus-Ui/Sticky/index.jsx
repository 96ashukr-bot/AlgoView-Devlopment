import React, { useState, Fragment, useEffect } from 'react';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';
import { StickyNote, AddNewNote } from '../../../Constant';
import axios from 'axios';
import { Breadcrumbs, H5 } from '../../../AbstractElements';
import { StickyApi } from '../../../api';

const Sticky = () => {

  const [notes, setNotes] = useState([]);

  useEffect(() => {
    axios.get(StickyApi).then(res => setNotes(res.data));
  }, []);

  const addStickyNote = () => {
    setNotes([...notes, { id: notes.length + 1, isDeleted: false }]);
  };

  const deleteNote = (note) => {
    setNotes([...notes, { id: note, isDeleted: true }]);
    note.isDeleted = true;
  };

  return (
    <Fragment>
      <Breadcrumbs mainTitle='Sticky Notes' parent="Bouns Ui" title="Sticky" />
      <Container fluid={true}>
        <Row className="sticky-header-main">
          <Col sm="12">
            <Card>
              <CardHeader>
                <H5>{StickyNote}
                  <a href="#javascript" onClick={addStickyNote} className="btn btn-primary pull-right m-l-10">{AddNewNote}</a>
                </H5>
              </CardHeader>
              <CardBody>
                <div className="sticky-note" id="board">
                  {notes.map((data, i) => (
                    <div className={`note ui-draggable ui-draggable-handle ${data.isDeleted ? 'd-none' : ''}`} key={i}>
                      <a href="# " onClick={() => deleteNote(data)} className="button remove" >{'X'}</a>
                      <div className="note_cnt">
                        <textarea className="title" placeholder="Enter note title" style={{ height: '64px' }}></textarea>
                        <textarea className="cnt" placeholder="Enter note description here" style={{ height: '200px' }}></textarea>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Sticky;