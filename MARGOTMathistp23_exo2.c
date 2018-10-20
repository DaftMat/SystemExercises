/*	MARGOT Mathis 21606171
 *	TP2 - Exercise 2 - System Programming
 *	Pipechain - Language : C
 *
 *	Compilation : gcc MARGOTMathistp23_exo2.c -o ex2
 *
 *	This program creates N processes (N given in parameter). The ith data (1 < i < N) reads
 *	the x pipe, gives new value to the data, and write it on the y pipe, the Nth pipe sends
 *	the data back to the first, which ends the program.
 *
 *	Note about the number of pipes : I tried my best to find a way to use a single pipe for more than 2 processes,
 *	but 3. It reveals it doesnt work properly, it make some of the processes useless, or make the program loop...
 */

#include <time.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

void afficherEtat(int nP, int nD, int msg, int nb);
void traitementPremier(int pipe_w, int nb, int msg);
void traitement(int pipe_r, int pipe_w);

int main(int argc, char *argv[]){
	int n = 0;
	
	time_t t;
	  
	/* Intializes random number generator */
	srand((unsigned) time(&t));

	//manage argv's
	if (argc != 2){
		perror("Usage : program [number of processes]");
		exit(77);
	}else{
		if ((n = atoi(argv[1])) < 0){
			perror ("Usage : program [number of processes] -> must be a positive integer");
			exit(88);
		}
	}

	int pipes[n][2];
	int msg = rand()%1000;
	pid_t pids[n-1];


	//Create pipes
	for (int i = 0 ; i < n/2+n%2 ; ++i){
		if (pipe(pipes[i]) == -1){
			perror("pipes error\n");
			exit(98);
		}
	}

	//Create n-1 processes (already having one : this)
	for (int i = 0 ; i < n-1 ; ++i){
		if ((pids[i] = fork()) == -1){
			perror("fork error");
			exit(99);
		}else if(pids[i] == 0){
			i = n;
			break;	//we only want to create processes from the first process.
		}
	}

	//communications
	for (int i = 0 ; i < n-1 ; ++i){//n-1 = first process + argv[1] processes
		if (pids[i] == 0){
			close(pipes[i][1]);	//will get from the last process
			close(pipes[i+1][0]);//will send to the next process
			traitement(pipes[i][0], pipes[i+1][1]);
			afficherEtat(i+2, (i+3==n+1 ? 1 : i+3), msg, i+2);
			printf("Processus de pid %d : je me termine (aussi)\n", getpid());
			exit(i);
		}
	}

	//first process
	close(pipes[0][0]);
	close(pipes[n-1][1]);
	traitementPremier(pipes[0][1], msg, 1);
	afficherEtat(1, 2, msg, 1);
	wait(NULL);
	int tmp;
	for (int i = 0 ; i < 3 ; ++i)	read(pipes[n-1][0], &tmp, sizeof(tmp));	//get the last elements
	close(pipes[n-1][0]);//close the last pipe
	printf("Processus de pid %d : L'information m'est revenue de %d, je peux me terminer\n", getpid(), n);
	return 0;
}

void afficherEtat(int nP, int nD, int msg, int nb){
	printf("Processus de pid %d : n %d dans l'anneau : j'envoie au n %d l'info [%d-%d-%d]\n", getpid(), nP, nD, getpid(), msg, nb);
}

void traitement(int pipe_r, int pipe_w){
	int pid = getpid();
	int prevPid;
	int msg;
	int nb;
	read(pipe_r, &prevPid, sizeof(prevPid));
	read(pipe_r, &msg, sizeof(msg));
	read(pipe_r, &nb, sizeof(nb));
	nb++;
	write(pipe_w, &pid, sizeof(pid));
	write(pipe_w, &msg, sizeof(msg));
	write(pipe_w, &nb, sizeof(nb));
	close(pipe_r);
	close(pipe_w);
}

void traitementPremier(int pipe_w, int nb, int msg){
	int pid = getpid();
	int tmp;
	write(pipe_w, &pid, sizeof(pid));
	write(pipe_w, &msg, sizeof(msg));
	write(pipe_w, &nb, sizeof(nb));
	close(pipe_w);
}
