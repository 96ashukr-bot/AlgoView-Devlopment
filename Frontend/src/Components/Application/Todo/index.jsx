import React, { Fragment, useContext, useState } from 'react';
import { Plus } from 'react-feather';
import { Card, CardBody, CardHeader, Col, Container, Row } from 'reactstrap';
import { Breadcrumbs, H5, Btn } from '../../../AbstractElements';
import { AddNewTask, AddTask, Close, ToDo } from '../../../Constant';
import TodoContext from '../../../_helper/Todo';
import TodoCheckbox from './TodoCheckbox';
import TodoList from './TodoList';
import TodoSideBar from './TodoSideBar';

const TodoContain = () => {
  const { addNewTodo } = useContext(TodoContext);

  const [addTask, setAddTask] = useState('');
  const [task, setTask] = useState('');
  const border_danger = useState('');
  const openTaskWrapper = () => {
    setAddTask(' visible');
    document.getElementById('addTaskBtn').classList.add('hide');
  };
  const closeTaskWrapper = () => {
    setAddTask('');
    document.getElementById('addTaskBtn').classList.remove('hide');
  };
  const onTaskChanged = (e) => {
    setTask({
      task: e.currentTarget.value,
    });
  };
  const addNewTask = () => {
    if (task === '') {
      document.getElementById('newtask').classList.remove('border-danger');
      document.getElementById('newtask').classList.add('border-danger');
    } else {
      addNewTodo(task);
      setAddTask(' visible');
      setTask('');
      document.getElementById('newtask').value = '';
      document.getElementById('newtask').classList.add('taskmag-hide');
      document.getElementById('newtask').classList.remove('taskmag-show');
      document.getElementById('addTaskBtn').classList.add('hide');
    }
  };
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Todo' parent='Apps' title='Todo' />
      <Container fluid={true} className='email-wrap bookmark-wrap todo-wrap'>
        <Row>
          <TodoSideBar />
          <Col xl='9' className='xl-70 box-col-12'>
            <Card>
              <CardHeader className='d-flex align-items-center justify-content-between'>
                <H5>{ToDo}</H5>
                <div className='d-flex align-items-center gap-3'>
                  <div className='todo'>
                    <div className='todo-list-wrapper'>
                      <TodoCheckbox />
                    </div>
                  </div>
                  <Btn attrBtn={{ color: 'primary d-flex align-items-center', onClick: openTaskWrapper }}>
                    <Plus style={{ width: '18px', height: '18px' }} className='me-2' /> {AddNewTask}
                  </Btn>
                </div>
              </CardHeader>
              <CardBody>
                <div className='todo'>
                  <div className='todo-list-wrapper'>
                    <div className='todo-list-container todo-list-footer'>
                      <div className={'new-task-wrapper mb-4' + addTask}>
                        <textarea className={'ng-untouched ng-pristine' + border_danger} id='newtask' placeholder='Enter new task here. . .' defaultValue={task} onChange={onTaskChanged}></textarea>
                        <Btn attrBtn={{ color: 'danger', className: 'cancel-btn', id: 'close-task-panel', onClick: closeTaskWrapper }}>{Close}</Btn>
                        <Btn attrBtn={{ color: 'success', className: 'ms-3 add-new-task-btn', id: 'add-task', onClick: addNewTask }}>{AddTask}</Btn>
                      </div>
                      <TodoList />
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default TodoContain;
