(defstruct task
  wcet period deadline wcrt y k)

(defvar rts 
  (list 
   (make-task :wcet 1 :period 3 :deadline 3) 
   (make-task :wcet 1 :period 4 :deadline 4) 
   (make-task :wcet 1 :period 6 :deadline 6)
   (make-task :wcet 1 :period 12 :deadline 12)))

(defmacro wcet ()
  `(task-wcet task))

(defmacro deadline ()
  `(task-deadline task))

(defmacro period ()
  `(task-period task))

(defmacro wcrt ()
  `(task-wcrt task))

(defmacro for-each-task (rts prop)
  `(mapcar (lambda (task) (,prop)) ,rts))

(defun u (task)
  "factor de utilizacion de la tarea task"
  (/ (wcet) (period)))

(defun hiperperiod (rts)
  "hiperperiodo de rts"
  (apply 'lcm (mapcar (lambda (task) (period)) rts)))

(defun uf (rts) 
  "calcula el factor de utilización del rts"
  (apply '+ (mapcar (lambda (task) (u task)) rts)))

(defun liu-bound (rts)
  "calcula la cota de liu y planificabilidad de rts"
  (* (length rts) (- (expt 2 (/ 1 (length rts))) 1)))

(defun test-liu-bound (rts)
  "comprueba si el rts cumple con la cota de liu"
  (if (>= (liu-bound rts) (uf rts)) t))

(defun test-bini-bound (rts)
  "comprueba si el rts cumple con la cota de bini"
  (if (>= 2 (apply '* (mapcar (lambda (task) (+ (u task) 1)) rts))) t))

(defun workload (rts time)
  "calcula la carga de trabajo del rts en el instante time"
  (apply '+ (mapcar (lambda (task) (* (fceiling time (period)) (wcet))) rts)))

(defun rta (rts)
  "calcula la planificabilidad mediante RTA"  
  (let* ((time 0))
    (loop for task in rts for i from 0 collect
          (let ((seed (+ time (wcet))))
             
                  (loop
                    (setf time seed)
                    (setf seed (+ (wcet) (workload (subseq rts 0 i) seed)))
                    (if (> seed (deadline)) (return nil))
                    (if (eq time seed) (return time)))))))

(defun rtaX (rts)
  "calcula la planificabilidad mediante RTA"  
  (let* ((time 0))
    (loop for task in rts for i from 0 collect
          (let ((seed (+ time (wcet))))
                (setf (task-wcrt task)
                  (loop
                    (setf time seed)
                    (setf seed (+ (wcet) (workload (subseq rts 0 i) seed)))
                    (if (> seed (deadline)) (return nil))
                    (if (eq time seed) (return time))))))))
                 

(defun promotion-times (rts)
  "calcula los tiempos de promocion de cada tarea en rts"
  (mapcar (lambda (task) (if  (wcrt) (- (deadline) (wcrt)))) rts))
  
(defun calculate-k (rts)
  "calcula los valores k de cada tarea en rts"
  (loop for task in rts for i from 0 collect
        (let ((time 0) (k 0))
             
                   (loop 
                      (setf w (+ k (workload (subseq rts 0 (+ i 1)) time)))
                      (if (eq time w) (incf k))
                      (setf time w)
                      (if (> time (deadline)) (return (- k 1)))))))

(defun free-slots (rts)
  "busca el primer slot libre"
  (let ((time 0))
    (loop for task in rts for i from 0 collect 
          (let ((seed (+ time (wcet))))
               (loop
                    (setf time seed)
                    (setf seed (+ 1 (workload (subseq rts 0 (+ i 1)) seed)))
                    (if (eq time seed) (return (- time 1))))))))

(defun eval-rts (rts)
  (format t "N:~10t~a~%" (length rts))
  (format t "H:~10t~a~%" (hiperperiod rts))
  (format t "UF:~10t~4,2f~%" (uf rts))
  (format t "LIU:~10t~a~%" (test-liu-bound rts))
  (format t "BINI:~10t~a~%" (test-bini-bound rts))
  (format t "RTA:~10t~a~%" (rta rts))
  (format t "Y:~10t~a~%" (promotion-times rts))
  (format t "K:~10t~a~%" (calculate-k rts))
  (format t "FREE:~10t~a~%" (free-slots rts)))

(eval-rts rts)


(print rts)
